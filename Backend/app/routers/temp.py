"""Router for inspecting and triggering temp collection logs in MongoDB Atlas."""
from __future__ import annotations

from fastapi import APIRouter
from ..config import get_settings
from .. import mongo_service

router = APIRouter(prefix="/api/temp", tags=["temp-logs"])


@router.get("")
def list_temp_logs(limit: int = 50):
    """List recent documents in the `temp` collection."""
    records = mongo_service.get_recent_temp_records(limit=limit)
    settings = get_settings()
    return {
        "ok": True,
        "database": settings.MONGODB_DB_NAME,
        "collection": "temp",
        "ttlHours": settings.TEMP_TTL_HOURS,
        "intervalMinutes": settings.TEMP_LOG_INTERVAL_MINUTES,
        "count": len(records),
        "records": records,
    }


@router.post("/trigger")
def trigger_temp_log():
    """Manually insert current timestamp into `temp` collection."""
    res = mongo_service.log_temp_timestamp()
    return {
        "ok": "error" not in res,
        "result": res,
    }
