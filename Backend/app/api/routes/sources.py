"""Sources API routes."""
from __future__ import annotations

import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_current_user
from ...config.mongo import get_mongo_db
from ...services.project_service import get_project
from ...utils.helpers import utcnow_iso

from ...services.source_service import delete_source as service_delete_source, get_source as service_get_source

router = APIRouter(tags=["sources"])


@router.post("/api/projects/{project_id}/sources", status_code=201)
async def create_source(
    project_id: str,
    payload: Dict[str, Any],
    user: dict = Depends(get_current_user),
):
    """Add a source to a project."""
    get_project(project_id, uid=user["uid"])
    source_id = payload.get("id") or f"src-{uuid.uuid4().hex[:8]}"
    now = utcnow_iso()

    source_doc = {
        "id": source_id,
        "sourceId": source_id,
        "projectId": project_id,
        "firebaseUid": user["uid"],
        "name": payload.get("name", "Untitled_Source.txt"),
        "type": payload.get("type", "TEXT"),
        "size": payload.get("size", "0 KB"),
        "pages": payload.get("pages", 1),
        "extractedText": payload.get("extractedText", ""),
        "status": "ready",
        "createdAt": now,
        "updatedAt": now,
    }

    mongo_db = get_mongo_db()
    mongo_db["sources"].update_one(
        {"id": source_id},
        {"$set": source_doc},
        upsert=True,
    )

    # Update project source record
    mongo_db["projects"].update_one(
        {"id": project_id},
        {"$set": {"source": source_doc, "sourceCount": 1, "updatedAt": now}},
    )

    return source_doc


@router.get("/api/projects/{project_id}/sources")
async def list_sources(
    project_id: str,
    user: dict = Depends(get_current_user),
):
    """List sources attached to the project."""
    get_project(project_id, uid=user["uid"])
    mongo_db = get_mongo_db()
    cursor = mongo_db["sources"].find(
        {"projectId": project_id, "$or": [{"firebaseUid": user["uid"]}, {"userId": user["uid"]}]},
        {"_id": 0},
    )
    items = list(cursor)
    return {"ok": True, "sources": items, "count": len(items)}


@router.get("/api/projects/{project_id}/sources/{source_id}")
async def get_source_by_id(
    project_id: str,
    source_id: str,
    user: dict = Depends(get_current_user),
):
    """Get single source details within a project."""
    get_project(project_id, uid=user["uid"])
    return service_get_source(source_id, user["uid"])


@router.get("/api/sources/{source_id}")
async def get_source_standalone(
    source_id: str,
    user: dict = Depends(get_current_user),
):
    """Get single source details by sourceId (cross-tenant protected)."""
    return service_get_source(source_id, user["uid"])


@router.delete("/api/sources/{source_id}")
async def delete_source_standalone(
    source_id: str,
    user: dict = Depends(get_current_user),
):
    """Delete a source by sourceId."""
    service_delete_source(source_id, user["uid"])
    return {"ok": True, "deleted": source_id}
