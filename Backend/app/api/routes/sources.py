"""Sources API routes."""
from __future__ import annotations

import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_workspace_identity
from ...storage.repository import get_repository
from ...services.projects.project_service import get_project
from ...services.sources.source_service import (
    delete_source as service_delete_source,
    get_source as service_get_source,
    list_sources as service_list_sources,
)
from ...utils.helpers import utcnow_iso

router = APIRouter(tags=["sources"])

sources_repo = get_repository("sources")
projects_repo = get_repository("projects")


@router.post("/api/projects/{project_id}/sources", status_code=201)
async def create_source(
    project_id: str,
    payload: Dict[str, Any],
    user: dict = Depends(get_workspace_identity),
):
    """Add a source to a project."""
    get_project(project_id, uid=user["uid"])
    source_id = payload.get("id") or f"src-{uuid.uuid4().hex[:8]}"
    now = utcnow_iso()

    source_doc = {
        "id": source_id,
        "sourceId": source_id,
        "projectId": project_id,
        "userId": user["uid"],
        "name": payload.get("name", "Untitled_Source.txt"),
        "type": payload.get("type", "TEXT"),
        "size": payload.get("size", "0 KB"),
        "pages": payload.get("pages", 1),
        "extractedText": payload.get("extractedText", ""),
        "status": "ready",
        "createdAt": now,
        "updatedAt": now,
    }

    sources_repo.update_one(
        {"id": source_id},
        {"$set": source_doc},
        upsert=True,
    )

    # Update project source record
    projects_repo.update_one(
        {"id": project_id},
        {"$set": {"source": source_doc, "sourceCount": 1, "updatedAt": now}},
    )

    return source_doc


@router.get("/api/projects/{project_id}/sources")
async def list_sources(
    project_id: str,
    user: dict = Depends(get_workspace_identity),
):
    """List sources attached to the project."""
    get_project(project_id, uid=user["uid"])
    items = service_list_sources(user["uid"], project_id=project_id)
    return {"ok": True, "sources": items, "count": len(items)}


@router.get("/api/projects/{project_id}/sources/{source_id}")
async def get_source_by_id(
    project_id: str,
    source_id: str,
    user: dict = Depends(get_workspace_identity),
):
    """Get single source details within a project."""
    get_project(project_id, uid=user["uid"])
    return service_get_source(source_id, user["uid"])


@router.get("/api/sources/{source_id}")
async def get_source_standalone(
    source_id: str,
    user: dict = Depends(get_workspace_identity),
):
    """Get single source details by sourceId (cross-tenant protected)."""
    return service_get_source(source_id, user["uid"])


@router.delete("/api/sources/{source_id}")
async def delete_source_standalone(
    source_id: str,
    user: dict = Depends(get_workspace_identity),
):
    """Delete a source by sourceId."""
    service_delete_source(source_id, user["uid"])
    return {"ok": True, "deleted": source_id}
