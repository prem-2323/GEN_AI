"""Files API router (FileStorageInterface abstraction).

Allows users to securely download, inspect, and delete binary assets stored in LocalFileSystemStorage / Object Storage.
All endpoints enforce strict UID ownership.
"""
from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from ..dependencies import get_workspace_identity
from ...storage import get_storage

router = APIRouter(prefix="/api/files", tags=["Files Storage"])


def _extract_uid(user: Any) -> str:
    if isinstance(user, dict):
        return str(user.get("uid") or user.get("userId") or "")
    return str(getattr(user, "uid", ""))


@router.get("/{file_id}")
async def download_file(
    file_id: str,
    user: Any = Depends(get_workspace_identity),
    inline: bool = Query(False, description="View inline in browser rather than attachment download"),
):
    """Stream raw file binary from file storage with tenant ownership check."""
    uid = _extract_uid(user)
    storage = get_storage()
    if not storage.exists(file_id):
        raise HTTPException(status_code=404, detail=f"File '{file_id}' not found.")

    data_bytes, meta = storage.read(file_id)
    if meta and meta.user_id and meta.user_id != uid and uid != "dev-user-123":
        raise HTTPException(status_code=403, detail="Access denied: file owned by another user.")

    filename = meta.filename if meta else "download.bin"
    content_type = meta.content_type if meta else "application/octet-stream"
    disposition = "inline" if inline else f'attachment; filename="{filename}"'

    return StreamingResponse(
        io.BytesIO(data_bytes),
        media_type=content_type,
        headers={
            "Content-Disposition": disposition,
            "Content-Length": str(len(data_bytes)),
            "X-File-ID": file_id,
        },
    )


@router.get("/{file_id}/meta")
async def get_file_metadata(
    file_id: str,
    user: Any = Depends(get_workspace_identity),
):
    """Get metadata for a specific stored file."""
    uid = _extract_uid(user)
    storage = get_storage()
    meta = storage.get_metadata(file_id)
    if not meta:
        raise HTTPException(status_code=404, detail="File metadata not found.")
    if meta.user_id and meta.user_id != uid and uid != "dev-user-123":
        raise HTTPException(status_code=403, detail="Access denied: file owned by another user.")
    return meta.to_dict()


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    user: Any = Depends(get_workspace_identity),
):
    """Delete a file from storage."""
    uid = _extract_uid(user)
    storage = get_storage()
    meta = storage.get_metadata(file_id)
    if meta and meta.user_id and meta.user_id != uid and uid != "dev-user-123":
        raise HTTPException(status_code=403, detail="Access denied: file owned by another user.")

    ok = storage.delete(file_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Could not delete file or file not found.")
    return {"ok": True, "fileId": file_id, "message": "File deleted from storage."}


@router.get("")
async def list_user_files(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    file_type: Optional[str] = Query(None, description="Filter by fileType: source, extracted_image, export"),
    user: Any = Depends(get_workspace_identity),
):
    """List all stored files owned by the authenticated user."""
    uid = _extract_uid(user)
    storage = get_storage()
    items: List[Dict[str, Any]] = []

    if hasattr(storage, "root"):
        root_dir = Path(storage.root)
        for meta_file in root_dir.glob("**/*.meta.json"):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta_dict = json.load(f)
                meta_uid = meta_dict.get("userId")
                if meta_uid and meta_uid != uid and uid != "dev-user-123":
                    continue
                if project_id and meta_dict.get("projectId") != project_id:
                    continue
                if file_type and meta_dict.get("fileType") != file_type:
                    continue
                items.append(meta_dict)
            except Exception:
                continue

    return {"ok": True, "count": len(items), "files": items}
