"""UCKR API Routes (Phase 4), Validation, and Temp Logs."""
from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from ..auth import get_current_user
from ...services.uckr.uckr_builder import (
    build_and_save_uckr,
    get_latest_uckr_record,
    get_uckr_validation_report,
    get_uckr_version,
    list_uckr_versions,
)
from ...services.validation_service import validate_deliverable
from ...config.mongo import get_recent_temp_records, log_temp_timestamp
from ...config.settings import get_settings
from ...utils.helpers import is_valid_id

router = APIRouter(tags=["uckr"])
uckr_router = APIRouter(prefix="/api/uckr", tags=["uckr"])
validation_router = APIRouter(prefix="/api/validation", tags=["validation"])
temp_router = APIRouter(prefix="/api/temp", tags=["temp-logs"])


def _check_id(val: str, name: str = "ID") -> None:
    if not is_valid_id(val):
        raise HTTPException(status_code=400, detail=f"Invalid {name} format.")


# ==========================================
# Phase 4: UCKR Endpoints
# ==========================================

@router.post("/api/projects/{project_id}/sources/{source_id}/uckr", status_code=201)
async def build_uckr_endpoint(
    project_id: str,
    source_id: str,
    user: dict = Depends(get_current_user),
):
    """Build or retrieve the canonical UCKR knowledge base for a source."""
    _check_id(project_id, "Project ID")
    _check_id(source_id, "Source ID")
    uckr = build_and_save_uckr(user["uid"], project_id, source_id, force_rebuild=False)
    return {
        "ok": True,
        "uckrId": uckr.get("uckrId"),
        "version": uckr.get("version", 1),
        "status": uckr.get("status", "valid"),
        "statistics": uckr.get("statistics") or uckr.get("stats") or {},
        "uckr": uckr,
    }


@router.get("/api/projects/{project_id}/sources/{source_id}/uckr")
async def get_source_uckr_endpoint(
    project_id: str,
    source_id: str,
    user: dict = Depends(get_current_user),
):
    """Get latest UCKR for a specific project source."""
    _check_id(project_id, "Project ID")
    _check_id(source_id, "Source ID")
    uckr = get_latest_uckr_record(project_id, user["uid"], source_id=source_id)
    return {"ok": True, "uckr": uckr}


@router.get("/api/projects/{project_id}/sources/{source_id}/uckr/validation")
async def get_source_uckr_validation_endpoint(
    project_id: str,
    source_id: str,
    user: dict = Depends(get_current_user),
):
    """Get deep validation and consistency report for source UCKR."""
    _check_id(project_id, "Project ID")
    _check_id(source_id, "Source ID")
    report = get_uckr_validation_report(project_id, source_id, user["uid"])
    return {"ok": True, "validation": report}


@router.post("/api/projects/{project_id}/sources/{source_id}/uckr/rebuild")
async def rebuild_source_uckr_endpoint(
    project_id: str,
    source_id: str,
    user: dict = Depends(get_current_user),
):
    """Force rebuild UCKR from latest AI analysis and increment version."""
    _check_id(project_id, "Project ID")
    _check_id(source_id, "Source ID")
    uckr = build_and_save_uckr(user["uid"], project_id, source_id, force_rebuild=True)
    return {
        "ok": True,
        "uckrId": uckr.get("uckrId"),
        "version": uckr.get("version", 1),
        "status": uckr.get("status", "valid"),
        "statistics": uckr.get("statistics") or uckr.get("stats") or {},
        "uckr": uckr,
    }


@router.get("/api/projects/{project_id}/sources/{source_id}/uckr/{version}")
async def get_source_uckr_version_endpoint(
    project_id: str,
    source_id: str,
    version: int,
    user: dict = Depends(get_current_user),
):
    """Get a specific historical version of UCKR for auditability."""
    _check_id(project_id, "Project ID")
    _check_id(source_id, "Source ID")
    uckr = get_uckr_version(project_id, source_id, version, user["uid"])
    return {"ok": True, "uckr": uckr}


# Legacy and Project-level convenience routes for frontend
@router.get("/api/projects/{project_id}/uckr")
async def get_project_uckr_latest(
    project_id: str,
    sourceId: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    """Project-level latest UCKR retrieval for UI display."""
    _check_id(project_id, "Project ID")
    uckr = get_latest_uckr_record(project_id, user["uid"], source_id=sourceId)
    return {"ok": True, "projectId": project_id, "uckr": uckr}


@router.get("/api/projects/{project_id}/uckr/versions")
async def list_project_uckr_versions(
    project_id: str,
    sourceId: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    _check_id(project_id, "Project ID")
    versions = list_uckr_versions(project_id, user["uid"], source_id=sourceId, limit=limit)
    return {"ok": True, "projectId": project_id, "versions": versions}


# ==========================================
# Legacy / Existing Validation & Temp Routes
# ==========================================

@validation_router.post("")
async def validate_output(payload: Dict[str, Any], user: dict = Depends(get_current_user)):
    deliv_type = payload.get("type", "generic")
    content = payload.get("content")
    source_text = payload.get("sourceText", "")
    return validate_deliverable(deliv_type, content, source_text)


@temp_router.get("")
async def list_temp_logs(limit: int = 50):
    settings = get_settings()
    records = get_recent_temp_records(limit=limit)
    return {
        "ok": True,
        "database": settings.mongodb_db_name,
        "collection": "temp",
        "ttlHours": settings.temp_ttl_hours,
        "intervalMinutes": settings.temp_log_interval_minutes,
        "count": len(records),
        "records": records,
    }


@temp_router.post("/trigger")
async def trigger_temp_log():
    res = log_temp_timestamp()
    return {"ok": "error" not in res, "result": res}
