"""Document Type Detector (Phase 3).

Detects file types (PDF, DOCX, TXT, MD, Images) using binary signatures, headers, and extensions.
"""
from __future__ import annotations

import os
from typing import Tuple

# Binary header signatures
_PDF_HEADER = b"%PDF-"
_ZIP_HEADER = b"PK\x03\x04"  # DOCX is a zip archive containing word/document.xml
_PNG_HEADER = b"\x89PNG\r\n\x1a\n"
_JPEG_HEADER = b"\xff\xd8\xff"


def detect_document_type(filename: str, content_bytes: bytes, mime_type: str = "") -> Tuple[str, str]:
    """Detect document file type and normalized extension from content signature and filename.

    Returns:
        Tuple[str, str]: (canonical_file_type, canonical_extension)
    """
    ext = (os.path.splitext(filename)[1] or "").lstrip(".").lower()

    # 1. Inspect magic signatures
    if content_bytes.startswith(_PDF_HEADER):
        return "pdf", "pdf"

    if content_bytes.startswith(_PNG_HEADER):
        return "image", "png"

    if content_bytes.startswith(_JPEG_HEADER):
        return "image", "jpg"

    if content_bytes.startswith(_ZIP_HEADER):
        # Could be docx, pptx, or generic zip
        if ext == "docx" or "wordprocessingml" in mime_type:
            return "docx", "docx"
        if ext == "pptx" or "presentationml" in mime_type:
            return "pptx", "pptx"
        if ext in ("xlsx",):
            return ext, ext

    # 2. Extension fallbacks
    if ext == "pdf":
        return "pdf", "pdf"
    if ext == "docx":
        return "docx", "docx"
    if ext == "pptx":
        return "pptx", "pptx"
    if ext in ("txt", "text", "csv", "log", "json"):
        return "txt", ext
    if ext in ("md", "markdown"):
        return "md", "md"
    if ext in ("png", "jpg", "jpeg", "webp", "gif", "bmp", "tiff"):
        return "image", ext

    return ext or "unknown", ext or "bin"
