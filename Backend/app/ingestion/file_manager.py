"""Document Storage and File Management (Phase 3).

Manages physical file layout under storage/documents/<document_id>/:
- original/   -> uploaded source file
- extracted/  -> text.json & metadata.json extracted output
- images/     -> extracted figures/images
- generated/  -> transformation outputs & exports
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import uuid
from pathlib import Path
from typing import Any, BinaryIO, Dict, Optional

from ..core.config import get_settings
from ..core.logging import get_logger
from ..storage.service import get_storage, save_original, sanitize_filename

log = get_logger("ingestion.file_manager")


def compute_sha256(data_bytes: bytes) -> str:
    """Calculate hex SHA-256 digest of data bytes."""
    return hashlib.sha256(data_bytes).hexdigest()


def generate_document_id(prefix: str = "src") -> str:
    """Generate a unique document identifier."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def save_original_file(
    uid: str,
    project_id: str,
    filename: str,
    data_bytes: bytes,
    source_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Save original file under storage/documents/<doc_id>/original/."""
    safe_name = sanitize_filename(filename)
    stream = io.BytesIO(data_bytes)
    return save_original(
        uid=uid,
        project_id=project_id,
        safe_name=safe_name,
        stream=stream,
        source_id=source_id,
    )


def save_extracted_content(
    document_id: str,
    extracted_data: Dict[str, Any],
    metadata_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """Save extracted/text.json and extracted/metadata.json under storage/documents/<doc_id>/extracted/."""
    storage = get_storage()
    
    text_key = f"documents/{document_id}/extracted/text.json"
    meta_key = f"documents/{document_id}/extracted/metadata.json"

    text_bytes = json.dumps(extracted_data, indent=2, default=str).encode("utf-8")
    storage.save(text_key, text_bytes)

    if metadata_data:
        meta_bytes = json.dumps(metadata_data, indent=2, default=str).encode("utf-8")
        storage.save(meta_key, meta_bytes)

    log.info("Saved extracted document content key=%s bytes=%d", text_key, len(text_bytes))
    return {
        "textKey": text_key,
        "metaKey": meta_key,
    }


def get_document_file_path(document_id: str, filename: str, subfolder: str = "original") -> Path:
    """Resolve storage path for document asset."""
    storage = get_storage()
    key = f"documents/{document_id}/{subfolder}/{filename}"
    return storage.get_path(key)


# Backward compatibility alias
save_file_to_storage = save_original_file
