"""Sources API routes."""
from __future__ import annotations

import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_current_user
from ...config.mongo import get_mongo_db
from ...services.project_service import get_project
from ...utils.helpers import utcnow_iso

router = APIRouter(prefix="/api/projects/{project_id}/sources", tags=["sources"])


@router.post("", status_code=201)
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


@router.get("", response_model=List[Dict[str, Any]])
async def list_sources(
    project_id: str,
    user: dict = Depends(get_current_user),
):
    """List sources attached to the project."""
    get_project(project_id, uid=user["uid"])
    mongo_db = get_mongo_db()
    cursor = mongo_db["sources"].find({"projectId": project_id}, {"_id": 0})
    return list(cursor)


@router.get("/{source_id}")
async def get_source_by_id(
    project_id: str,
    source_id: str,
    user: dict = Depends(get_current_user),
):
    """Get single source details."""
    get_project(project_id, uid=user["uid"])
    mongo_db = get_mongo_db()
    doc = mongo_db["sources"].find_one({"projectId": project_id, "id": source_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Source not found.")
    return doc
