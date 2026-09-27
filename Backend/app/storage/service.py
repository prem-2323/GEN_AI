"""Local File System Storage Abstraction for binary files and output deliverables."""
from __future__ import annotations

import io
import logging
import os
import re
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..core.config import get_settings

log = logging.getLogger("gen-transform.storage_service")


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and invalid characters."""
    clean = os.path.basename(filename)
    clean = re.sub(r"[^\w\.\-]", "_", clean)
    return clean or "unnamed_file"


class LocalFileSystemStorage:
    """Storage provider for document uploads, exports, and generated assets."""

    def __init__(self, root_dir: Optional[str] = None) -> None:
        settings = get_settings()
        self.root_dir = Path(root_dir or settings.storage_root).resolve()
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _full_path(self, relative_path: str) -> Path:
        rel = relative_path.lstrip("/\\")
        return (self.root_dir / rel).resolve()

    def get_path(self, relative_path: str) -> Path:
        """Get absolute Path object for a storage key."""
        return self._full_path(relative_path)

    def exists(self, relative_path: str) -> bool:
        return self._full_path(relative_path).exists()

    def write(self, relative_path: str, content: bytes) -> str:
        dest = self._full_path(relative_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        return relative_path

    # Alias for write
    def save(self, relative_path: str, content: bytes) -> str:
        return self.write(relative_path, content)

    def read(self, relative_path: str) -> Tuple[bytes, str]:
        path = self._full_path(relative_path)
        if not path.exists():
            raise FileNotFoundError(f"Storage path does not exist: {relative_path}")
        return path.read_bytes(), path.name

    def delete(self, relative_path: str) -> bool:
        path = self._full_path(relative_path)
        if path.exists():
            path.unlink()
            return True
        return False


_STORAGE_INSTANCE: Optional[LocalFileSystemStorage] = None


def get_storage() -> LocalFileSystemStorage:
    """Get active file storage provider instance."""
    global _STORAGE_INSTANCE
    if _STORAGE_INSTANCE is None:
        _STORAGE_INSTANCE = LocalFileSystemStorage()
    return _STORAGE_INSTANCE


def absolute_storage_path(relative_path: str) -> Path:
    """Return absolute Path object for relative storage path."""
    return get_storage().get_path(relative_path)


def save_output(relative_path: str, data: bytes) -> str:
    """Helper to save generated output deliverable file into storage."""
    storage = get_storage()
    return storage.write(relative_path, data)


def read_file_bytes(relative_path: str) -> bytes:
    """Helper to read raw bytes of a file from storage."""
    storage = get_storage()
    content, _ = storage.read(relative_path)
    return content


def save_original(
    uid: str,
    project_id: str,
    safe_name: str,
    stream: Any,
    source_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Save original file under storage/documents/<doc_id>/original/."""
    doc_id = source_id or f"doc-{uuid.uuid4().hex[:12]}"
    rel_path = f"documents/{doc_id}/original/{safe_name}"
    if isinstance(stream, (bytes, bytearray)):
        data = bytes(stream)
    elif hasattr(stream, "read"):
        data = stream.read()
    else:
        data = b""

    storage = get_storage()
    storage.save(rel_path, data)
    return {
        "documentId": doc_id,
        "storagePath": rel_path,
        "filename": safe_name,
        "bytes": len(data),
    }


def save_extracted_image(doc_id: str, image_bytes: bytes, extension: str = "png") -> str:
    """Save extracted image/figure under storage/documents/<doc_id>/images/."""
    img_id = f"img_{uuid.uuid4().hex[:8]}.{extension}"
    rel_path = f"documents/{doc_id}/images/{img_id}"
    storage = get_storage()
    storage.save(rel_path, image_bytes)
    return rel_path


__all__ = [
    "LocalFileSystemStorage",
    "get_storage",
    "absolute_storage_path",
    "save_output",
    "read_file_bytes",
    "save_original",
    "save_extracted_image",
    "sanitize_filename",
]
