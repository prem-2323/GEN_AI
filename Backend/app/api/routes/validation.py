"""Validation API Routes (Phase 13 Validation & Consistency Engine).

Endpoints:
- POST /api/validation/validate
- POST /api/validation/consistency
- GET  /api/validation/{validation_id}
- Legacy consistency validation routes
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import get_workspace_identity
from ...models.validation import RegenerateRequest, ValidationRecord, ValidationRequest as LegacyValidationRequest
from ...services.consistency import (
    get_latest_validation,
    regenerate_deliverable_with_feedback,
    validate_project_sources,
    validate_single_deliverable,
)
from ...services.transformation.transformation_service import get_single_deliverable
from ...storage.repository import get_repository
from ...validation.schemas import (
    CrossOutputConsistencyResult,
    ValidationRequest as Phase13ValidationRequest,
    ValidationResult,
)
from ...validation.service import ValidationService, get_validation_service

router = APIRouter(tags=["consistency_validation"])


# ---------------------------------------------------------------------------
# Phase 13 Validation Engine Endpoints
# ---------------------------------------------------------------------------
@router.post(
    "/api/validation/validate",
    response_model=ValidationResult,
    status_code=status.HTTP_200_OK,
    summary="Validate generated transformation output against source ground truth",
)
def validate_transformation_output(
    payload: Phase13ValidationRequest,
) -> ValidationResult:
    """Audit generated transformation output for factual, numeric, date, entity, and citation errors."""
    service: ValidationService = get_validation_service()
    try:
        result = service.validate(payload)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation execution failed: {e}",
        )


@router.post(
    "/api/validation/consistency",
    response_model=CrossOutputConsistencyResult,
    status_code=status.HTTP_200_OK,
    summary="Evaluate cross-output consistency across multiple deliverables",
)
def evaluate_cross_output_consistency(
    payload: Dict[str, str],
) -> CrossOutputConsistencyResult:
    """Compare multiple generated deliverables for factual discrepancies."""
    service: ValidationService = get_validation_service()
    try:
        return service.evaluate_consistency(payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Consistency evaluation failed: {e}",
        )


@router.get(
    "/api/validation/{validation_id}",
    response_model=ValidationResult,
    summary="Retrieve validation result by ID",
)
def get_validation_result_by_id(validation_id: str) -> ValidationResult:
    """Retrieve validation result by ID."""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Validation record '{validation_id}' not found in active cache.",
    )


# ---------------------------------------------------------------------------
# Legacy Validation Endpoints
# ---------------------------------------------------------------------------
@router.post(
    "/api/projects/{project_id}/sources/{source_id}/validate",
    response_model=ValidationRecord,
    status_code=status.HTTP_200_OK,
    summary="Run Consistency Engine validation on source deliverables",
)
async def validate_source_deliverables(
    project_id: str,
    source_id: str,
    payload: Optional[LegacyValidationRequest] = None,
    user: Dict[str, Any] = Depends(get_workspace_identity),
):
    """Audits all generated deliverables against the canonical UCKR single source of truth."""
    req = payload or LegacyValidationRequest()
    return validate_project_sources(project_id, source_id, req, user)


@router.get(
    "/api/projects/{project_id}/sources/{source_id}/validation",
    summary="Get latest validation audit report for source",
)
async def get_validation_report(
    project_id: str,
    source_id: str,
    user: Dict[str, Any] = Depends(get_workspace_identity),
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
    user: Dict[str, Any] = Depends(get_workspace_identity),
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
    user: Dict[str, Any] = Depends(get_workspace_identity),
):
    """Regenerates a deliverable using validation error feedback and re-validates."""
    req = payload or RegenerateRequest()
    return regenerate_deliverable_with_feedback(project_id, deliverable_id, req, user)


__all__ = ["router"]
