"""Phase 12 Transformation Engine — API Router.

Exposes REST API endpoints for document transformation, profile listing,
type discovery, and preview generation.
"""

from __future__ import annotations

from typing import List
from fastapi import APIRouter, HTTPException, status

from ...transformation.schemas import (
    TransformationPreviewResponse,
    TransformationProfile,
    TransformationRequest,
    TransformationResponse,
)
from ...transformation.service import TransformationService, get_transformation_service

router = APIRouter(prefix="/api/transformation", tags=["Transformation Engine"])


@router.post(
    "/transform",
    response_model=TransformationResponse,
    summary="Transform source knowledge/evidence into structured deliverable",
)
def transform_document(
    request: TransformationRequest,
) -> TransformationResponse:
    """Execute document transformation deliverable request."""
    service: TransformationService = get_transformation_service()
    try:
        response = service.transform(request)
        return response
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transformation execution failed: {e}",
        )


@router.get(
    "/types",
    response_model=List[str],
    summary="List all supported output types",
)
def list_output_types() -> List[str]:
    """Retrieve list of all supported transformation output type names."""
    service: TransformationService = get_transformation_service()
    return service.registry.list_output_types()


@router.get(
    "/profiles",
    response_model=List[TransformationProfile],
    summary="List all transformation profiles",
)
def list_transformation_profiles() -> List[TransformationProfile]:
    """Retrieve all registered output type profiles with structural requirements."""
    service: TransformationService = get_transformation_service()
    return service.registry.list_profiles()


@router.post(
    "/preview",
    response_model=TransformationPreviewResponse,
    summary="Preview transformation structure and profile without full inference",
)
def preview_transformation(
    request: TransformationRequest,
) -> TransformationPreviewResponse:
    """Generate transformation preview."""
    service: TransformationService = get_transformation_service()
    try:
        return service.preview_transformation(request)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{transformation_id}",
    response_model=TransformationResponse,
    summary="Get transformation result by ID",
)
def get_transformation_by_id(transformation_id: str) -> TransformationResponse:
    """Retrieve details for a completed transformation ID (mock/cached)."""
    # For demonstration/cached lookup, generate dummy lookup response or 404
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Transformation ID '{transformation_id}' not found in active cache.",
    )


__all__ = ["router"]
