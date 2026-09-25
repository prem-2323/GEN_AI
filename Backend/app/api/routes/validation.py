"""Validation API Routes (Phase 7 Consistency Engine).

Endpoints:
- POST /api/projects/{project_id}/sources/{source_id}/validate
- GET  /api/projects/{project_id}/sources/{source_id}/validation
- POST /api/projects/{project_id}/deliverables/{deliverable_id}/validate
- POST /api/projects/{project_id}/deliverables/{deliverable_id}/regenerate
- POST /api/projects/{project_id}/validate (project-level convenience)
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from ...auth import get_current_user
from ...models.validation import RegenerateRequest, ValidationRecord, ValidationRequest
from ...services.consistency import (
    get_latest_validation,
    regenerate_deliverable_with_feedback,
    validate_project_sources,
    validate_single_deliverable,
)
from ...services.transformation.transformation_service import get_single_deliverable
from ...storage.repository import get_repository

router = APIRouter(tags=["consistency_validation"])


@router.post(
    "/api/projects/{project_id}/sources/{source_id}/validate",
    response_model=ValidationRecord,
    status_code=status.HTTP_200_OK,
    summary="Run Consistency Engine validation on source deliverables",
)
async def validate_source_deliverables(
    project_id: str,
    source_id: str,
    payload: Optional[ValidationRequest] = None,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Audits all generated deliverables against the canonical UCKR single source of truth."""
    req = payload or ValidationRequest()
    return validate_project_sources(project_id, source_id, req, user)


@router.get(
    "/api/projects/{project_id}/sources/{source_id}/validation",
    summary="Get latest validation audit report for source",
)
async def get_validation_report(
    project_id: str,
    source_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Retrieves the latest validation audit report with exact check breakdown and scores."""
    return get_latest_validation(project_id, source_id, user)


@router.post(
    "/api/projects/{project_id}/deliverables/{deliverable_id}/validate",
    summary="Validate a single deliverable against UCKR",
)
async def validate_individual_deliverable(
    project_id: str,
    deliverable_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Validates an individual deliverable against canonical UCKR."""
    deliv = get_single_deliverable(project_id, deliverable_id, user)
    source_id = deliv.get("sourceId")
    uckr_version = deliv.get("uckrVersion", 1)

    uckr_repo = get_repository("uckr")
    uckr_doc = None
    if source_id:
        uckr_doc = uckr_repo.find_one({"projectId": project_id, "sourceId": source_id, "version": uckr_version})
        if not uckr_doc:
            uckr_doc = uckr_repo.find_one({"projectId": project_id, "sourceId": source_id}, sort=[("version", -1)])
    if not uckr_doc:
        uckr_doc = uckr_repo.find_one({"projectId": project_id}, sort=[("version", -1)])

    if not uckr_doc:
        raise HTTPException(status_code=404, detail="Canonical UCKR document not found.")

    res = validate_single_deliverable(uckr_doc, deliv)
    return {"ok": True, "result": res.model_dump()}


@router.post(
    "/api/projects/{project_id}/deliverables/{deliverable_id}/regenerate",
    summary="Regenerate deliverable with validation error feedback constraints",
)
async def regenerate_deliverable(
    project_id: str,
    deliverable_id: str,
    payload: Optional[RegenerateRequest] = None,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Regenerates a deliverable using validation error feedback and re-validates."""
    req = payload or RegenerateRequest()
    return regenerate_deliverable_with_feedback(project_id, deliverable_id, req, user)
