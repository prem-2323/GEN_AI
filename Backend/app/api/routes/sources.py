"""Sources API — Phase 2 flow with ownership + state machine.

    POST /api/projects/{id}/upload  (multipart file)
    GET  /api/projects/{id}/sources
    GET  /api/sources/{source_id}
    DELETE /api/sources/{source_id}
"""
from __future__ import annotations

import io
import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..auth import get_current_user
from ...services import source_service, storage_service
from ...services.extraction_service import extract_normalized
from ...services.project_service import get_project, update_project
from ...utils.helpers import is_valid_id

log = logging.getLogger("gen-transform.routes.sources")
router = APIRouter(tags=["sources"])


def _check_pid(project_id: str) -> None:
    if not is_valid_id(project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID format.")


@router.post("/api/projects/{project_id}/upload")
async def upload_source(
    project_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    uid = user["uid"]
    _check_pid(project_id)
    project = get_project(project_id, uid)  # ownership gate

    raw = await file.read()
    safe_name, ext = storage_service.validate_upload(
        file.filename or "upload.bin", len(raw), file.content_type or "")

    stored = storage_service.save_original(uid, project_id, safe_name,
                                           io.BytesIO(raw))
    src = source_service.create_source(uid, project_id, {
        "originalName": safe_name,
        "storedName": stored["storedName"],
        "mimeType": file.content_type or "application/octet-stream",
        "size": stored["size"],
        "storagePath": stored["storagePath"],
    })
    try:
        source_service.set_stage(src["sourceId"], uid, "validating", 10)
        source_service.set_stage(src["sourceId"], uid, "extracting", 40)
        normalized = extract_normalized(raw, safe_name, ext, uid, project_id,
                                        src["sourceId"], persist_images=True)
        if not normalized["text"]["content"] and not normalized.get("images"):
            raise ValueError("No extractable text or images found in file.")
        source_service.store_extraction(src["sourceId"], uid, normalized)
        done = source_service.set_stage(src["sourceId"], uid, "completed", 100)
    except HTTPException:
        raise
    except Exception as exc:
        log.warning("extraction failed source=%s: %s", src["sourceId"], exc)
        source_service.set_stage(src["sourceId"], uid, "failed", error=str(exc)[:500])
        raise HTTPException(status_code=422, detail=f"Extraction failed: {exc}")

    try:
        update_project(project_id, {
            "sourceCount": source_service.count_project_sources(uid, project_id),
            "status": "source_ready",
        }, uid)
    except HTTPException:
        pass
    return {"ok": True, "projectId": project_id, "source": done}


@router.get("/api/projects/{project_id}/sources")
async def list_project_sources(project_id: str, user: dict = Depends(get_current_user),
                               limit: int = 50):
    _check_pid(project_id)
    get_project(project_id, user["uid"])
    return {"ok": True, "projectId": project_id,
            "sources": source_service.list_sources(user["uid"], project_id, limit)}


@router.get("/api/sources/{source_id}")
async def get_source(source_id: str, user: dict = Depends(get_current_user)):
    return {"ok": True, "source": source_service.get_source(source_id, user["uid"])}


@router.delete("/api/sources/{source_id}")
async def delete_source(source_id: str, user: dict = Depends(get_current_user)):
    source_service.delete_source(source_id, user["uid"])
    return {"ok": True, "deleted": source_id}
