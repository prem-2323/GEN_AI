"""Pipeline API — Phases 3-11.

    POST /api/projects/{id}/analyze      {sourceId}              -> UCKR
    GET  /api/projects/{id}/uckr[?sourceId] / versions
    POST /api/projects/{id}/transform    {types[], config}       -> 7 deliverables
    GET  /api/projects/{id}/deliverables
    POST /api/projects/{id}/validate     -> consistency report
    GET  /api/projects/{id}/validations
    POST /api/projects/{id}/jobs         {sourceId, outputs?}    -> background pipeline
    GET  /api/jobs/{job_id}  |  GET /api/projects/{id}/jobs
    POST /api/deliverables/{id}/export?format=md|json|pptx
    GET  /api/search?q=&kind=  |  GET /api/projects/{id}/overview
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from ..auth import get_current_user
from ...services import (
    ai_orchestrator,
    export_service,
    job_service,
    search_service,
    source_service,
    transformation_service,
    uckr_service,
    validation_service,
)
from ...services.project_service import get_project
from ...utils.helpers import is_valid_id

router = APIRouter(tags=["pipeline"])


def _check_pid(project_id: str) -> None:
    if not is_valid_id(project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID format.")


# ---- Phase 3+4: analyse -> UCKR ----
@router.post("/api/projects/{project_id}/analyze")
async def analyze_source(project_id: str, payload: dict[str, Any],
                         user: dict = Depends(get_current_user)):
    uid = user["uid"]
    _check_pid(project_id)
    source_id = (payload or {}).get("sourceId", "")
    if not source_id:
        raise HTTPException(status_code=422, detail="sourceId is required.")
    src = source_service.get_source(source_id, uid)
    if src.get("projectId") != project_id:
        raise HTTPException(status_code=400, detail="Source does not belong to this project.")
    norm = src.get("normalized")
    if not norm:
        raise HTTPException(status_code=409, detail="Source has no extraction yet.")
    analysis = ai_orchestrator.analyze_text(norm["text"]["content"],
                                            use_cache_on_source=src if src.get("analysis") else None)
    uckr = uckr_service.build_and_save(uid, project_id, source_id, analysis, norm)
    return {"ok": True, "uckr": uckr, "analysisProvider": analysis.get("provider")}


@router.get("/api/projects/{project_id}/uckr")
async def get_uckr(project_id: str, user: dict = Depends(get_current_user),
                   sourceId: Optional[str] = None):
    _check_pid(project_id)
    return {"ok": True, "uckr": uckr_service.get_latest_uckr(project_id, user["uid"], sourceId)}


@router.get("/api/projects/{project_id}/uckr/versions")
async def list_uckrs(project_id: str, user: dict = Depends(get_current_user)):
    _check_pid(project_id)
    return {"ok": True, "versions": uckr_service.list_uckrs(project_id, user["uid"])}


# ---- Phase 5: transform ----
@router.post("/api/projects/{project_id}/transform")
async def transform(project_id: str, payload: dict[str, Any],
                    user: dict = Depends(get_current_user)):
    _check_pid(project_id)
    types = (payload or {}).get("types") or (payload or {}).get("selectedOutputs") or []
    if not types:
        raise HTTPException(status_code=422, detail="types[] is required (max 7).")
    made = transformation_service.generate_many(
        user["uid"], project_id, list(types)[:7], (payload or {}).get("config"))
    return {"ok": True, "count": len(made), "deliverables": made}


@router.get("/api/projects/{project_id}/deliverables")
async def list_deliverables(project_id: str, user: dict = Depends(get_current_user)):
    _check_pid(project_id)
    return {"ok": True,
            "deliverables": transformation_service.list_deliverables(user["uid"], project_id)}


# ---- Phase 6: validate ----
@router.post("/api/projects/{project_id}/validate")
async def validate(project_id: str, user: dict = Depends(get_current_user)):
    _check_pid(project_id)
    return {"ok": True, "validation": validation_service.validate_project(user["uid"], project_id)}


@router.get("/api/projects/{project_id}/validations")
async def list_validations(project_id: str, user: dict = Depends(get_current_user)):
    _check_pid(project_id)
    return {"ok": True,
            "validations": validation_service.list_validations(user["uid"], project_id)}


# ---- Phase 7: jobs ----
@router.post("/api/projects/{project_id}/jobs", status_code=201)
async def start_job(project_id: str, payload: dict[str, Any],
                    background: BackgroundTasks, user: dict = Depends(get_current_user)):
    _check_pid(project_id)
    source_id = (payload or {}).get("sourceId", "")
    if not source_id:
        raise HTTPException(status_code=422, detail="sourceId is required.")
    job = job_service.create_job(user["uid"], project_id, source_id,
                                 (payload or {}).get("type", "full_transformation"),
                                 {"outputs": (payload or {}).get("outputs"),
                                  "config": (payload or {}).get("config")})
    background.add_task(job_service.run_full_transformation, job["jobId"], user["uid"])
    return {"ok": True, "job": job}


@router.get("/api/jobs/{job_id}")
async def get_job(job_id: str, user: dict = Depends(get_current_user)):
    return {"ok": True, "job": job_service.get_job(job_id, user["uid"])}


@router.get("/api/projects/{project_id}/jobs")
async def list_jobs(project_id: str, user: dict = Depends(get_current_user)):
    _check_pid(project_id)
    return {"ok": True, "jobs": job_service.list_jobs(user["uid"], project_id)}


# ---- Phase 10: export ----
@router.post("/api/deliverables/{deliverable_id}/export")
async def export_one(deliverable_id: str, user: dict = Depends(get_current_user),
                     format: str = "md"):
    return export_service.export_deliverable(user["uid"], deliverable_id, format)


# ---- Phase 9/11: search + overview ----
@router.get("/api/search")
async def search(q: str = "", kind: str = "all", user: dict = Depends(get_current_user)):
    if kind not in ("all", "project", "source"):
        raise HTTPException(status_code=422, detail="kind must be all|project|source.")
    return {"ok": True, **search_service.search(user["uid"], q, kind)}


@router.get("/api/projects/{project_id}/overview")
async def overview(project_id: str, user: dict = Depends(get_current_user)):
    _check_pid(project_id)
    get_project(project_id, user["uid"])
    return {"ok": True, **search_service.project_overview(user["uid"], project_id)}
