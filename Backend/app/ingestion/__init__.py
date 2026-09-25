"""Document Ingestion Module: upload validation, storage management, and extraction pipeline entry."""
from __future__ import annotations

from .file_manager import generate_document_id, save_file_to_storage, compute_sha256
from .service import IngestionService, ingestion_service
from .validator import sanitize_filename, validate_file_upload

__all__ = [
    "IngestionService",
    "ingestion_service",
    "validate_file_upload",
    "sanitize_filename",
    "generate_document_id",
    "save_file_to_storage",
    "compute_sha256",
]
