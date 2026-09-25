"""Transformation API Routes (Phase 6).

Endpoints:
- POST /api/projects/{project_id}/transform
- GET /api/projects/{project_id}/deliverables
- GET /api/projects/{project_id}/deliverables/{deliverable_id}
- DELETE /api/projects/{project_id}/deliverables/{deliverable_id}
- POST /api/transform (general legacy compatibility)
"""
from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from ...auth import get_current_user
from ...models.deliverable import TransformationRequest, TransformResponse
from ...services.transformation.transformation_service import (
    transform_content as run_transformation,
    get_project_deliverables,
    get_single_deliverable,
    delete_single_deliverable,
)

router = APIRouter(tags=["transformations"])


@router.get(
    "/api/projects/{project_id}/deliverables/{deliverable_id}",
    summary="Get single deliverable by ID",
)
async def get_deliverable_by_id(
    project_id: str,
    deliverable_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Retrieves a single deliverable with full provenance metadata."""
    doc = get_single_deliverable(project_id, deliverable_id, user)
    return {"ok": True, "deliverable": doc}


@router.delete(
    "/api/projects/{project_id}/deliverables/{deliverable_id}",
    summary="Delete single deliverable",
)
async def delete_deliverable_by_id(
    project_id: str,
    deliverable_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Deletes a deliverable record."""
    return delete_single_deliverable(project_id, deliverable_id, user)


@router.post("/api/transform", summary="Legacy transform route")
async def legacy_transform(
    payload: Dict[str, Any],
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Legacy compatibility endpoint."""
    project_id = payload.get("projectId") or payload.get("project_id")
    if not project_id:
        return {"ok": True, "message": "Specify project_id for full UCKR transformation"}
    
    req = TransformationRequest(
        sourceId=payload.get("sourceId"),
        uckrVersion=payload.get("uckrVersion"),
        outputTypes=payload.get("selectedOutputs") or payload.get("outputTypes") or ["linkedin"],
        configuration=payload.get("config") or payload.get("configuration") or {},
    )
    return run_transformation(project_id, req, user)
