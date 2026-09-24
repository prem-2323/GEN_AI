"""Upload API routes for projects and standalone documents."""
from __future__ import annotations

import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..auth import get_current_user
from ...services.extraction_service import extract_content, extract_normalized
from ...services.project_service import get_project
from ...services.source_service import create_source, get_source, set_stage, store_extraction
from ...services.storage_service import save_original, validate_upload
import io

log = logging.getLogger("gen-transform.upload")

router = APIRouter(tags=["upload"])


@router.post("/api/projects/{project_id}/upload")
async def upload_project_source(
    project_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Upload a source document to a project and run extraction."""
    uid = user["uid"]
    get_project(project_id, uid=uid)

    contents = await file.read()
    filename = file.filename or "upload.bin"
    size = len(contents)

    # 1. Validation
    safe_name, mime_type = validate_upload(filename, size, file.content_type or "")

    # 2. Save file to MongoDB GridFS & disk
    saved = save_original(uid, project_id, safe_name, io.BytesIO(contents))
    rel_path = saved["storagePath"]
    stored_name = saved["storedName"]
    file_id = saved.get("fileId", "")

    # 3. Create Source Record
    file_meta = {
        "originalName": filename,
        "storedName": stored_name,
        "mimeType": mime_type,
        "size": size,
        "storagePath": rel_path,
        "fileId": file_id,
        "sha256": saved.get("sha256", ""),
    }
    src_doc = create_source(uid, project_id, file_meta)
    sid = src_doc["sourceId"]

    # 4. State transitions: validating -> extracting -> completed
    try:
        set_stage(sid, uid, "validating", 20)
        set_stage(sid, uid, "extracting", 50)

        # 5. Extract text, tables, pages
        ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else "txt"
        normalized = extract_normalized(
            contents,
            filename=filename,
            ext=ext,
            uid=uid,
            project_id=project_id,
            source_id=sid,
        )

        # 6. Store extraction & complete
        final_doc = store_extraction(sid, uid, normalized)
        final_doc = set_stage(sid, uid, "completed", 100)

        return {
            "ok": True,
            "source": final_doc,
        }
    except Exception as exc:
        log.error("Source extraction failed for %s: %s", sid, exc)
        set_stage(sid, uid, "failed", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Source extraction failed: {exc}")


@router.post("/api/upload")
async def upload_source(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Standalone lightweight source upload & extraction endpoint."""
    contents = await file.read()
    result = extract_content(contents, filename=file.filename or "source.txt", mime_type=file.content_type or "")
    return {
        "ok": True,
        "source": result,
    }
