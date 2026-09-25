"""Document storage and file management."""
from __future__ import annotations

import hashlib
import io
import os
import uuid
from typing import BinaryIO, Dict, Any, Tuple

from ..core.config import get_settings
from ..core.logging import get_logger

log = get_logger("ingestion.file_manager")


def compute_sha256(data_bytes: bytes) -> str:
    """Calculate hex SHA-256 digest of data bytes."""
    return hashlib.sha256(data_bytes).hexdigest()


def generate_document_id(prefix: str = "src") -> str:
    """Generate a unique document identifier."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def save_file_to_storage(
    uid: str,
    project_id: str,
    filename: str,
    data_bytes: bytes,
    mime_type: str = "",
) -> Dict[str, Any]:
    """Save original file to disk storage and MongoDB GridFS (if available)."""
    settings = get_settings()
    sha256_hash = compute_sha256(data_bytes)
    prefix = uuid.uuid4().hex[:8]
    stored_name = f"{prefix}_{filename}"

    # 1. Local disk directory
    project_dir = os.path.join(settings.storage_root, "uploads", uid, project_id)
    os.makedirs(project_dir, exist_ok=True)
    file_path = os.path.join(project_dir, stored_name)

    with open(file_path, "wb") as f:
        f.write(data_bytes)

    rel_path = f"uploads/{uid}/{project_id}/{stored_name}"
    file_id = ""

    # 2. GridFS storage
    try:
        from ..services.storage.gridfs_service import upload_gridfs_file
        file_id = upload_gridfs_file(
            uid=uid,
            project_id=project_id,
            filename=filename,
            data=data_bytes,
            content_type=mime_type or "application/octet-stream",
            file_type="source",
            extra_meta={"sha256": sha256_hash, "originalName": filename},
        )
    except Exception as exc:
        log.warning("GridFS upload skipped for %s: %s", filename, exc)

    return {
        "storedName": stored_name,
        "storagePath": rel_path,
        "fileId": file_id,
        "sha256": sha256_hash,
        "size": len(data_bytes),
    }
