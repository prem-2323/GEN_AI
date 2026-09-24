"""Transform API route."""
from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, Depends
from ..auth import get_current_user
from ...services.transformation_service import run_pipeline

router = APIRouter(prefix="/api/transform", tags=["transform"])


@router.post("")
async def transform_content(payload: Dict[str, Any], user: dict = Depends(get_current_user)):
    source = payload.get("source", {})
    config = payload.get("config", {})
    selected_outputs = payload.get("selectedOutputs", [])
    result = run_pipeline(source, config, selected_outputs)
    return {"ok": True, "result": result}
