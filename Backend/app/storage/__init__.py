"""Storage package re-exporting repository and file storage abstractions."""
from __future__ import annotations

from .repository import JSONDocumentRepository, get_repository
from .service import LocalFileSystemStorage, get_storage, save_output, read_file_bytes

__all__ = [
    "JSONDocumentRepository",
    "get_repository",
    "LocalFileSystemStorage",
    "get_storage",
    "save_output",
    "read_file_bytes",
]
