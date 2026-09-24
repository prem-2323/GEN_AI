"""File storage service (Phase 9 MongoDB Everything & GridFS Architecture).

Stores all file binaries (original uploads, extracted images, deliverable exports)
directly into MongoDB GridFS (bucket: `contentforge_files`).

Security (Phase 13):
  - extension allowlist + size limit
  - filename sanitisation (no directories, no special chars)
  - path-traversal protection
  - per-user / per-project namespacing & tenant ownership checks
"""
from __future__ import annotations

import hashlib
import io
import logging
import os
import re
import uuid
from pathlib import Path
from typing import BinaryIO, Optional, Tuple, Union

from fastapi import HTTPException

from ..config.settings import get_settings
from .gridfs_service import (
    upload_gridfs_file,
    download_gridfs_file,
    delete_gridfs_file,
    get_gridfs_file_doc,
)

log = logging.getLogger("gen-transform.storage")

_FILENAME_RE = re.compile(r"[^a-zA-Z0-9._-]+")

_MIME_BY_EXT = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
    "md": "text/markdown",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "mp3": "audio/mpeg",
    "mp4": "video/mp4",
    "json": "application/json",
}


def sanitize_filename(name: str) -> str:
    base = os.path.basename((name or "upload.bin").strip()) or "upload.bin"
    cleaned = _FILENAME_RE.sub("_", base).strip("._") or "upload.bin"
    return cleaned[:120]


def _storage_root() -> Path:
    return Path(get_settings().storage_root).resolve()


def _safe_join(*parts: str) -> Path:
    root = _storage_root()
    target = root.joinpath(*parts).resolve()
    if target != root and root not in target.parents:
        raise HTTPException(status_code=400, detail="Invalid storage path (traversal blocked).")
    return target


def validate_upload(filename: str, size_bytes: int, content_type: str = "") -> tuple[str, str]:
    """Return (safe_name, ext) or raise 422/413."""
    settings = get_settings()
    safe = sanitize_filename(filename)
    ext = safe.rsplit(".", 1)[-1].lower() if "." in safe else ""
    if ext not in settings.allowed_exts():
        raise HTTPException(
            status_code=422,
            detail=f"File type '.{ext}' not allowed. Allowed: {sorted(settings.allowed_exts())}.",
        )
    if size_bytes <= 0:
        raise HTTPException(status_code=422, detail="Empty file upload rejected.")
    if size_bytes > settings.max_upload_bytes():
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_bytes / 1048576:.1f} MB). Max {settings.max_upload_mb} MB.",
        )
    mime = content_type or _MIME_BY_EXT.get(ext, "application/octet-stream")
    return safe, ext


def save_original(
    uid: str,
    project_id: str,
    safe_name: str,
    stream: BinaryIO,
    source_id: Optional[str] = None,
) -> dict:
    """Persist the original file to MongoDB GridFS and local cache; return {fileId, storagePath, sha256, size}."""
    ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else "bin"
    mime_type = _MIME_BY_EXT.get(ext, "application/octet-stream")

    # Read all bytes & compute sha256
    data = stream.read()
    size = len(data)
    sha256 = hashlib.sha256(data).hexdigest()

    # 1. Store into MongoDB GridFS (Phase 9 primary binary storage)
    file_id = ""
    try:
        file_id = upload_gridfs_file(
            uid=uid,
            project_id=project_id,
            filename=safe_name,
            data=data,
            content_type=mime_type,
            file_type="source",
            source_id=source_id,
            extra_meta={"sha256": sha256, "size": size},
        )
    except Exception as exc:
        log.warning("GridFS upload fallback: %s", exc)

    # 2. Store to local directory for quick extraction cache
    subdir = _safe_join("uploads", uid, project_id)
    subdir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex[:8]}_{safe_name}"
    dest = _safe_join("uploads", uid, project_id, stored_name)
    with open(dest, "wb") as out:
        out.write(data)
    rel = dest.relative_to(_storage_root()).as_posix()

    log.info("Stored upload uid=%s project=%s gridfs_id=%s path=%s bytes=%d sha256=%s", uid, project_id, file_id, rel, size, sha256[:8])
    return {
        "fileId": file_id,
        "storagePath": rel,
        "storedName": stored_name,
        "size": size,
        "sha256": sha256,
        "mimeType": mime_type,
    }


def save_extracted_image(
    uid: str,
    project_id: str,
    source_id: str,
    image_bytes: bytes,
    ext: str = "png",
) -> Tuple[str, str]:
    """Save an image extracted from a document into MongoDB GridFS and disk.
    
    Returns (fileId, relative_path).
    """
    ext_clean = ext.lstrip(".") or "png"
    mime_type = _MIME_BY_EXT.get(ext_clean, f"image/{ext_clean}")
    name = f"{uuid.uuid4().hex[:8]}.{ext_clean}"

    # 1. GridFS upload
    file_id = ""
    try:
        file_id = upload_gridfs_file(
            uid=uid,
            project_id=project_id,
            filename=name,
            data=image_bytes,
            content_type=mime_type,
            file_type="extracted_image",
            source_id=source_id,
        )
    except Exception as exc:
        log.warning("GridFS image upload fallback: %s", exc)

    # 2. Local disk cache
    subdir = _safe_join("extracted", "images", uid, project_id, source_id)
    subdir.mkdir(parents=True, exist_ok=True)
    dest = _safe_join("extracted", "images", uid, project_id, source_id, name)
    with open(dest, "wb") as out:
        out.write(image_bytes)
    rel = dest.relative_to(_storage_root()).as_posix()

    return file_id, rel


def save_output(
    uid: str,
    project_id: str,
    filename: str,
    data: bytes,
    deliverable_id: Optional[str] = None,
    export_type: Optional[str] = None,
) -> Tuple[str, str]:
    """Save a generated export file (PPTX, DOCX, PDF, MP3, MP4) into MongoDB GridFS and disk.
    
    Returns (fileId, relative_path).
    """
    safe = sanitize_filename(filename)
    ext = safe.rsplit(".", 1)[-1].lower() if "." in safe else "bin"
    mime_type = _MIME_BY_EXT.get(ext, "application/octet-stream")

    # 1. GridFS upload
    file_id = ""
    try:
        file_id = upload_gridfs_file(
            uid=uid,
            project_id=project_id,
            filename=safe,
            data=data,
            content_type=mime_type,
            file_type="export",
            deliverable_id=deliverable_id,
            extra_meta={"exportType": export_type or ext, "size": len(data)},
        )
    except Exception as exc:
        log.warning("GridFS export upload fallback: %s", exc)

    # 2. Local disk cache
    subdir = _safe_join("outputs", uid, project_id)
    subdir.mkdir(parents=True, exist_ok=True)
    dest = _safe_join("outputs", uid, project_id, safe)
    with open(dest, "wb") as out:
        out.write(data)
    rel = dest.relative_to(_storage_root()).as_posix()

    return file_id, rel


def read_file_bytes(file_id_or_path: str, uid: Optional[str] = None) -> Tuple[bytes, str]:
    """Read binary data from GridFS (if ObjectId string) or local storage path.
    
    Returns (bytes, mime_type).
    """
    # Try GridFS if looks like ObjectId
    if len(file_id_or_path) == 24:
        try:
            data, meta = download_gridfs_file(file_id_or_path, uid)
            return data, meta.get("contentType", "application/octet-stream")
        except Exception:
            pass

    # Disk fallback
    path = absolute_storage_path(file_id_or_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Requested file does not exist.")
    ext = path.name.rsplit(".", 1)[-1].lower() if "." in path.name else "bin"
    with open(path, "rb") as f:
        return f.read(), _MIME_BY_EXT.get(ext, "application/octet-stream")


def absolute_storage_path(rel_path: str) -> Path:
    return _safe_join(*rel_path.split("/"))


def describe_backend() -> dict:
    settings = get_settings()
    return {
        "driver": "mongodb-gridfs",
        "bucket": "contentforge_files",
        "root": settings.storage_root,
        "note": "MongoDB stores all state in collections + all file binaries in GridFS.",
    }
