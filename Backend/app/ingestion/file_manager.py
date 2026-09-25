"""Document storage and file management."""
from __future__ import annotations

import hashlib
import io
import os
import uuid
from typing import BinaryIO, Dict, Any, Tuple

from ..core.config import get_settings
from ..core.logging import get_logger
from ..storage.service import save_original, sanitize_filename

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
    """Save original file using clean file storage service."""
    safe_name = sanitize_filename(filename)
    stream = io.BytesIO(data_bytes)
    return save_original(
        uid=uid,
        project_id=project_id,
        safe_name=safe_name,
        stream=stream,
    )

