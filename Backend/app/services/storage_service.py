"""File storage service (Phase 2 local dirs, Phase 8 Firebase Storage hook).

Security (Phase 13):
  - extension allowlist + size limit
  - filename sanitisation (no directories, no special chars)
  - path-traversal protection (resolved path must stay under storage root)
  - per-user / per-project namespacing: {root}/uploads/{uid}/{projectId}/
"""
from __future__ import annotations

import logging
import os
import re
import uuid
from pathlib import Path
from typing import BinaryIO

from fastapi import HTTPException

from ..config.settings import get_settings

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


def save_original(uid: str, project_id: str, safe_name: str, stream: BinaryIO) -> dict:
    """Persist the original file; return {storagePath, ...} (path relative to storage root)."""
    subdir = _safe_join("uploads", uid, project_id)
    subdir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex[:8]}_{safe_name}"
    dest = _safe_join("uploads", uid, project_id, stored_name)
    size = 0
    with open(dest, "wb") as out:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            out.write(chunk)
    rel = dest.relative_to(_storage_root()).as_posix()
    log.info("Stored upload uid=%s project=%s path=%s bytes=%d", uid, project_id, rel, size)
    return {"storagePath": rel, "storedName": stored_name, "size": size}


def save_extracted_image(uid: str, project_id: str, source_id: str, image_bytes: bytes, ext: str = "png") -> str:
    """Save an image extracted from a document; return path relative to storage root."""
    subdir = _safe_join("extracted", "images", uid, project_id, source_id)
    subdir.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex[:8]}.{ext.lstrip('.') or 'png'}"
    dest = _safe_join("extracted", "images", uid, project_id, source_id, name)
    with open(dest, "wb") as out:
        out.write(image_bytes)
    return dest.relative_to(_storage_root()).as_posix()


def save_output(uid: str, project_id: str, filename: str, data: bytes) -> str:
    """Save a generated export file; return path relative to storage root."""
    safe = sanitize_filename(filename)
    subdir = _safe_join("outputs", uid, project_id)
    subdir.mkdir(parents=True, exist_ok=True)
    dest = _safe_join("outputs", uid, project_id, safe)
    with open(dest, "wb") as out:
        out.write(data)
    return dest.relative_to(_storage_root()).as_posix()


def absolute_storage_path(rel_path: str) -> Path:
    return _safe_join(*rel_path.split("/"))


def describe_backend() -> dict:
    settings = get_settings()
    return {
        "driver": "firebase-storage" if settings.firebase_storage_bucket else "local",
        "root": settings.storage_root,
        "bucket": settings.firebase_storage_bucket or None,
        "note": "MongoDB stores metadata + storagePath only; bytes live in storage.",
    }
