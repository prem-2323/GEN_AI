"""GridFS Files API router (Phase 9 — MongoDB Everything & GridFS).

Allows users to securely download, inspect, and delete binary assets stored in MongoDB GridFS.
All endpoints enforce strict Firebase UID ownership.
"""
from __future__ import annotations

import io
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse

from ...auth import get_current_user
from ...services.gridfs_service import (
    download_gridfs_file,
    delete_gridfs_file,
    get_gridfs_file_doc,
    get_gridfs_files_collection,
)

router = APIRouter(prefix="/api/files", tags=["GridFS Files"])


def _extract_uid(user: Any) -> str:
    if isinstance(user, dict):
        return str(user.get("uid") or user.get("userId") or "")
    return str(getattr(user, "uid", ""))


@router.get("/{file_id}")
async def download_file(
    file_id: str,
    user: Any = Depends(get_current_user),
    inline: bool = Query(False, description="View inline in browser rather than attachment download"),
):
    """Stream raw file binary from MongoDB GridFS with tenant ownership check."""
    uid = _extract_uid(user)
    data_bytes, meta = download_gridfs_file(file_id, uid=uid)
    filename = meta.get("filename", "download.bin")
    content_type = meta.get("contentType") or "application/octet-stream"
    disposition = "inline" if inline else f'attachment; filename="{filename}"'

    return StreamingResponse(
        io.BytesIO(data_bytes),
        media_type=content_type,
        headers={
            "Content-Disposition": disposition,
            "Content-Length": str(len(data_bytes)),
            "X-GridFS-File-ID": file_id,
        },
    )


@router.get("/{file_id}/meta")
async def get_file_metadata(
    file_id: str,
    user: Any = Depends(get_current_user),
):
    """Get metadata for a specific GridFS file."""
    uid = _extract_uid(user)
    doc = get_gridfs_file_doc(file_id, uid=uid)
    if not doc:
        raise HTTPException(status_code=404, detail="File metadata not found.")
    return doc


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    user: Any = Depends(get_current_user),
):
    """Delete a file from MongoDB GridFS."""
    uid = _extract_uid(user)
    ok = delete_gridfs_file(file_id, uid=uid)
    if not ok:
        raise HTTPException(status_code=404, detail="Could not delete file or file not found.")
    return {"ok": True, "fileId": file_id, "message": "File deleted from GridFS."}


@router.get("")
async def list_user_files(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    file_type: Optional[str] = Query(None, description="Filter by fileType: source, extracted_image, export"),
    user: Any = Depends(get_current_user),
):
    """List all GridFS files owned by the authenticated user."""
    uid = _extract_uid(user)
    files_col = get_gridfs_files_collection()
    query: Dict[str, Any] = {
        "$or": [
            {"metadata.firebaseUid": uid},
            {"metadata.userId": uid},
        ]
    }
    if project_id:
        query["metadata.projectId"] = project_id
    if file_type:
        query["metadata.fileType"] = file_type

    cursor = files_col.find(query).sort("uploadDate", -1).limit(100)
    items: List[Dict[str, Any]] = []
    for doc in cursor:
        meta = doc.get("metadata", {})
        items.append({
            "fileId": str(doc["_id"]),
            "filename": doc.get("filename"),
            "length": doc.get("length"),
            "uploadDate": doc.get("uploadDate"),
            "contentType": meta.get("contentType"),
            "fileType": meta.get("fileType"),
            "projectId": meta.get("projectId"),
            "sourceId": meta.get("sourceId"),
            "deliverableId": meta.get("deliverableId"),
        })
    return {"ok": True, "count": len(items), "files": items}
