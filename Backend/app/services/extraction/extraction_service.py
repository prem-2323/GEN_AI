"""Compatibility shim re-exporting extraction service from app.extraction."""
from __future__ import annotations

from ...extraction.service import (
    ExtractionService,
    extract_content,
    extract_docx,
    extract_image,
    extract_normalized,
    extract_pdf,
    extract_pptx,
    extract_textlike,
)

__all__ = [
    "ExtractionService",
    "extract_normalized",
    "extract_content",
    "extract_pdf",
    "extract_docx",
    "extract_pptx",
    "extract_textlike",
    "extract_image",
]
