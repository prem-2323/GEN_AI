"""UCKR, Validation, and Temp Logs routes."""
from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, Depends
from ..auth import get_current_user
from ...services.project_service import get_project
from ...services.uckr_service import extract_uckr_from_text
from ...services.validation_service import validate_deliverable
from ...config.mongo import get_recent_temp_records, log_temp_timestamp
from ...config.settings import get_settings

uckr_router = APIRouter(prefix="/api/uckr", tags=["uckr"])
validation_router = APIRouter(prefix="/api/validation", tags=["validation"])
temp_router = APIRouter(prefix="/api/temp", tags=["temp-logs"])


# UCKR
@uckr_router.get("/{project_id}")
async def get_project_uckr(project_id: str, user: dict = Depends(get_current_user)):
    project = get_project(project_id, uid=user["uid"])
    return {"ok": True, "projectId": project_id, "uckr": project.get("uckr")}


# Validation
@validation_router.post("")
async def validate_output(payload: Dict[str, Any], user: dict = Depends(get_current_user)):
    deliv_type = payload.get("type", "generic")
    content = payload.get("content")
    source_text = payload.get("sourceText", "")
    return validate_deliverable(deliv_type, content, source_text)


# Temp Logs (30-min interval, 24-hr TTL MongoDB Atlas)
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
