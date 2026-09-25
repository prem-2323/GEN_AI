"""Job queue (Phase 7) — Database-independent `jobs` repository + stage machine + progress.

Pipeline stages:
    queued -> extracting -> analyzing_text -> analyzing_images
           -> building_uckr -> generating_outputs -> validating
           -> completed | failed

Jobs run in FastAPI BackgroundTasks; the frontend polls GET /api/jobs/{id}.
"""
from __future__ import annotations

import asyncio
import logging
import traceback
import uuid
from typing import Any, Optional

from fastapi import HTTPException
from ...storage.repository import get_repository
from ...utils.helpers import utcnow_iso

log = logging.getLogger("gen-transform.jobs")

STAGES = ("queued", "extracting", "analyzing_text", "analyzing_images",
          "building_uckr", "generating_outputs", "validating", "completed", "failed")
TERMINAL = {"completed", "failed"}


def _owner_filter(uid: str) -> dict:
    return {"$or": [{"userId": uid}, {"firebaseUid": uid}]}


def create_job(uid: str, project_id: str, source_id: str, job_type: str = "full_transformation",
               params: Optional[dict] = None) -> dict:
    from ..projects.project_service import get_project
    from ..sources import source_service

    get_project(project_id, uid)
    src = source_service.get_source(source_id, uid)
    if src.get("projectId") != project_id:
        raise HTTPException(status_code=400, detail="Source does not belong to this project.")
    now = utcnow_iso()
    doc = {
        "jobId": f"job-{uuid.uuid4().hex[:12]}",
        "userId": uid,
        "userId": uid,
        "projectId": project_id,
        "sourceId": source_id,
        "type": job_type,
        "status": "queued",
        "stage": "queued",
        "progress": 0,
        "params": params or {"outputs": ["linkedin", "twitter", "advisory", "executive_summary",
                                         "infographic", "presentation", "video"]},
        "result": {},
        "error": None,
        "createdAt": now,
        "updatedAt": now,
    }
    repo = get_repository("jobs")
    repo.insert_one(doc)
    return doc


def _update(job_id: str, **fields) -> None:
    fields["updatedAt"] = utcnow_iso()
    repo = get_repository("jobs")
    repo.update_one({"jobId": job_id}, {"$set": fields})


def get_job(job_id: str, uid: str) -> dict:
    repo = get_repository("jobs")
    doc = repo.find_one({"jobId": job_id, **_owner_filter(uid)}, projection={"_id": 0})
    if not doc:
        other = repo.find_one({"jobId": job_id}, projection={"_id": 0})
        if other:
            raise HTTPException(status_code=403, detail="Access denied. You do not own this job.")
        raise HTTPException(status_code=404, detail="Job not found.")
    return doc


def list_jobs(uid: str, project_id: str, limit: int = 20) -> list[dict]:
    from ..projects.project_service import get_project

    get_project(project_id, uid)
    repo = get_repository("jobs")
    return repo.find({"projectId": project_id, **_owner_filter(uid)}, sort=[("createdAt", -1)], limit=limit, projection={"_id": 0})


def run_full_transformation(job_id: str, uid: str) -> None:
    """Background worker: extraction -> AI -> UCKR -> outputs -> validation."""
    from ..sources import source_service
    from ..ai import pipeline_orchestrator as ai_orchestrator
    from ..uckr import pipeline_uckr as uckr_service
    from ..transformation import pipeline_transformation as transformation_service
    from ..validation import validation_service
    from ...storage import get_storage

    try:
        job = get_job(job_id, uid)
        project_id, source_id = job["projectId"], job["sourceId"]
        params = job.get("params", {})
        outputs = params.get("outputs") or ["linkedin", "twitter", "advisory", "executive_summary",
                                             "infographic", "presentation", "video"]

        _update(job_id, status="processing", stage="extracting", progress=10)
        src = source_service.get_source(source_id, uid)
        if (src.get("processing") or {}).get("stage") in ("completed", "failed"):
            src = source_service.reset_for_retry(source_id, uid)
        source_service.set_stage(source_id, uid, "validating", 15)
        source_service.set_stage(source_id, uid, "extracting", 30)
        rel = (src.get("file") or {}).get("storagePath", "")
        storage = get_storage()
        raw = storage.read(rel)[0] if rel and storage.exists(rel) else b""
        ext = ((src.get("file") or {}).get("originalName", "").rsplit(".", 1) + ["txt"])[-1].lower()

        from ..extraction.extraction_service import extract_normalized

        normalized = extract_normalized(raw, (src.get("file") or {}).get("originalName", "source"),
                                        ext, uid, project_id, source_id, persist_images=True)
        source_service.store_extraction(source_id, uid, normalized)
        source_service.set_stage(source_id, uid, "completed", 100)

        _update(job_id, stage="analyzing_text", progress=35)
        cached = src.get("analysis")
        analysis = ai_orchestrator.analyze_text(normalized["text"]["content"],
                                                use_cache_on_source=src if cached else None)

        _update(job_id, stage="analyzing_images", progress=50)
        visuals = []
        imgs = [(im.get("imageId", f"IMG-{i}"), im.get("path", "")) for i, im in enumerate(normalized.get("images", []))]
        existing = [(iid, absolute_storage_path(p).read_bytes()) for iid, p in imgs if p and absolute_storage_path(p).exists()]
        if existing:
            try:
                visuals = asyncio.run(ai_orchestrator.analyze_images_async(existing))
            except RuntimeError:
                loop = asyncio.new_event_loop()
                try:
                    visuals = loop.run_until_complete(ai_orchestrator.analyze_images_async(existing))
                finally:
                    loop.close()

        _update(job_id, stage="building_uckr", progress=65)
        uckr = uckr_service.build_and_save(uid, project_id, source_id, analysis, normalized)
        if visuals:
            uckr_repo = get_repository("uckr")
            uckr_repo.update_one({"uckrId": uckr["uckrId"]}, {"$set": {"visuals": visuals}})

        _update(job_id, stage="generating_outputs", progress=80)
        made = transformation_service.generate_many(uid, project_id, outputs, params.get("config"))

        _update(job_id, stage="validating", progress=92)
        try:
            validation = validation_service.validate_project(uid, project_id)
            vstatus: Any = validation.get("status")
        except HTTPException:
            vstatus = "skipped"

        _update(job_id, status="completed", stage="completed", progress=100,
                result={"uckrVersion": uckr.get("version"), "uckrId": uckr.get("uckrId"),
                        "deliverables": [d["type"] for d in made], "validation": vstatus})
        log.info("job completed %s project=%s", job_id, project_id)
    except Exception as exc:  # noqa: BLE001 — job must never crash the worker silently
        log.error("job %s failed: %s\n%s", job_id, exc, traceback.format_exc())
        _update(job_id, status="failed", stage="failed", error=str(exc)[:2000])
        try:
            jobs_repo = get_repository("jobs")
            job = jobs_repo.find_one({"jobId": job_id}, projection={"_id": 0})
            if job:
                from ..sources import source_service as _ss

                try:
                    _ss.set_stage(job["sourceId"], uid, "failed", error=str(exc)[:500])
                except HTTPException:
                    pass
        except Exception:
            pass

