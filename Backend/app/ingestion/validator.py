"""Document upload validation logic."""
from __future__ import annotations

import os
import re
from typing import Tuple

from ..core.config import get_settings
from ..core.constants import MIME_TYPE_MAP
from ..core.exceptions import DocumentValidationError

_UNSAFE_CHARS_RE = re.compile(r"[^\w\.\-\s]")


def sanitize_filename(filename: str) -> str:
    """Strip path components and unsafe characters from filenames."""
    base = os.path.basename(filename or "upload.bin").strip()
    safe = _UNSAFE_CHARS_RE.sub("_", base)
    if not safe or safe.startswith("."):
        safe = f"file_{safe}" if safe else "upload.bin"
    return safe[:128]


def validate_file_upload(
    filename: str,
    size_bytes: int,
    content_type: str = "",
) -> Tuple[str, str]:
    """Validate uploaded file attributes against allowed limits and extensions.
    
    Returns:
        Tuple[str, str]: (sanitized_filename, resolved_mime_type)
    """
    settings = get_settings()

    if size_bytes <= 0:
        raise DocumentValidationError("File is empty (0 bytes).")

    max_bytes = settings.max_upload_bytes()
    if size_bytes > max_bytes:
        max_mb = settings.max_upload_mb
        raise DocumentValidationError(
            f"File size ({size_bytes / (1024*1024):.1f} MB) exceeds maximum allowed size ({max_mb} MB)."
        )

    safe_name = sanitize_filename(filename)
    ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
    allowed = settings.allowed_exts()

    if ext not in allowed:
        raise DocumentValidationError(
            f"File extension '.{ext}' is not supported. Allowed formats: {', '.join(sorted(allowed))}."
        )

    mime = (content_type or "").strip().lower()
    if not mime or mime == "application/octet-stream":
        mime = MIME_TYPE_MAP.get(ext, "application/octet-stream")

    return safe_name, mime
