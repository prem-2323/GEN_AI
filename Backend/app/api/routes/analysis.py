"""Phase 3 AI Content Understanding routes."""
from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..auth import get_current_user
from ...models.analysis import AnalysisRecord
from ...services.ai.analysis_service import analyze_source, get_analysis, get_analysis_status

router = APIRouter(prefix="/api/projects/{project_id}/sources/{source_id}/analysis", tags=["analysis"])


class AnalyzeRequest(BaseModel):
    extractedText: Optional[str] = None
    extractedImages: Optional[list] = None
    forceRefresh: bool = False


@router.post("", response_model=AnalysisRecord)
@router.post("/analyze", response_model=AnalysisRecord, include_in_schema=False)
async def start_analysis(
    project_id: str,
    source_id: str,
    payload: Optional[AnalyzeRequest] = None,
    user: dict = Depends(get_current_user),
):
    """Start or retrieve AI Content Understanding (Qwen text + Gemma vision) for a source."""
    text = payload.extractedText if payload else None
    images = payload.extractedImages if payload else None
    refresh = payload.forceRefresh if payload else False

    return analyze_source(
        project_id=project_id,
        source_id=source_id,
        firebase_uid=user["uid"],
        extracted_text=text,
        extracted_images=images,
        force_refresh=refresh,
    )


@router.get("", response_model=AnalysisRecord)
async def get_source_analysis(
    project_id: str,
    source_id: str,
    user: dict = Depends(get_current_user),
):
    """Get the structured AI analysis (facts, entities, events, metrics, visual evidence)."""
    return get_analysis(project_id=project_id, source_id=source_id, firebase_uid=user["uid"])


@router.get("/status")
async def get_source_analysis_status(
    project_id: str,
    source_id: str,
    user: dict = Depends(get_current_user),
):
    """Check analysis progress and pipeline stage."""
    return get_analysis_status(project_id=project_id, source_id=source_id, firebase_uid=user["uid"])


@router.post("/retry", response_model=AnalysisRecord)
async def retry_source_analysis(
    project_id: str,
    source_id: str,
    payload: Optional[AnalyzeRequest] = None,
    user: dict = Depends(get_current_user),
):
    """Force re-run AI Content Understanding on the source."""
    text = payload.extractedText if payload else None
    images = payload.extractedImages if payload else None

    return analyze_source(
        project_id=project_id,
        source_id=source_id,
        firebase_uid=user["uid"],
        extracted_text=text,
        extracted_images=images,
        force_refresh=True,
    )
