"""Job queue (Phase 7) — MongoDB `jobs` + stage machine + progress.

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
from pymongo import DESCENDING

from ..config.mongo import get_mongo_db
from ..utils.helpers import utcnow_iso

log = logging.getLogger("gen-transform.jobs")

STAGES = ("queued", "extracting", "analyzing_text", "analyzing_images",
          "building_uckr", "generating_outputs", "validating", "completed", "failed")
TERMINAL = {"completed", "failed"}


def _owner_filter(uid: str) -> dict:
    return {"$or": [{"firebaseUid": uid}, {"userId": uid}]}


def create_job(uid: str, project_id: str, source_id: str, job_type: str = "full_transformation",
               params: Optional[dict] = None) -> dict:
    from .project_service import get_project
    from . import source_service

    get_project(project_id, uid)
    src = source_service.get_source(source_id, uid)
    if src.get("projectId") != project_id:
        raise HTTPException(status_code=400, detail="Source does not belong to this project.")
    now = utcnow_iso()
    doc = {
        "jobId": f"job-{uuid.uuid4().hex[:12]}",
        "firebaseUid": uid,
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
    get_mongo_db()["jobs"].insert_one({**doc})
    doc.pop("_id", None)
    return doc


def _update(job_id: str, **fields) -> None:
    fields["updatedAt"] = utcnow_iso()
    get_mongo_db()["jobs"].update_one({"jobId": job_id}, {"$set": fields})


def get_job(job_id: str, uid: str) -> dict:
    doc = get_mongo_db()["jobs"].find_one({"jobId": job_id, **_owner_filter(uid)}, {"_id": 0})
    if not doc:
        other = get_mongo_db()["jobs"].find_one({"jobId": job_id}, {"jobId": 1})
        if other:
            raise HTTPException(status_code=403, detail="Access denied. You do not own this job.")
        raise HTTPException(status_code=404, detail="Job not found.")
    return doc


def list_jobs(uid: str, project_id: str, limit: int = 20) -> list[dict]:
    from .project_service import get_project

    get_project(project_id, uid)
    cur = get_mongo_db()["jobs"].find(
        {"projectId": project_id, **_owner_filter(uid)}, {"_id": 0}
    ).sort("createdAt", DESCENDING).limit(limit)
    return list(cur)


def run_full_transformation(job_id: str, uid: str) -> None:
    """Background worker: extraction -> AI -> UCKR -> outputs -> validation."""
    from . import source_service, ai_orchestrator, uckr_service
    from . import transformation_service, validation_service
    from .storage_service import absolute_storage_path

    db = get_mongo_db()
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
        raw = absolute_storage_path(rel).read_bytes() if rel else b""
        ext = ((src.get("file") or {}).get("originalName", "").rsplit(".", 1) + ["txt"])[-1].lower()

        from .extraction_service import extract_normalized

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
        existing = [(iid, absolute_storage_path(p).read_bytes()) for iid, p in imgs if p]
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
            db["uckr"].update_one({"uckrId": uckr["uckrId"]}, {"$set": {"visuals": visuals}})

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
            job = db["jobs"].find_one({"jobId": job_id}, {"projectId": 1, "sourceId": 1})
            if job:
                from . import source_service as _ss

                try:
                    _ss.set_stage(job["sourceId"], uid, "failed", error=str(exc)[:500])
                except HTTPException:
                    pass
        except Exception:
            pass
