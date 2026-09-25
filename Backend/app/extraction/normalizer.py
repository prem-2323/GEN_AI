"""Text Normalization Module (Phase 3).

Cleans and normalizes extracted text:
- Unicode NFKC normalization
- Whitespace normalization (tab -> space, trailing spaces)
- Newline cleanup (unifying CRLF -> LF, consolidating excessive blank lines)
- Page break / header / footer marker cleanup
- Preserves original text meaning for Phase 4 DocLink processing
"""
from __future__ import annotations

import re
import unicodedata

_MULTIPLE_NEWLINES_RE = re.compile(r"\n{3,}")
_TRAILING_SPACES_RE = re.compile(r"[ \t]+\n")
_TABS_RE = re.compile(r"\t+")
_NULL_BYTES_RE = re.compile(r"\x00")
_PAGE_NUMBER_HEADER_RE = re.compile(r"^\s*Page\s+\d+(\s+of\s+\d+)?\s*$", re.IGNORECASE)


def normalize_text(text: str) -> str:
    """Perform clean text normalization on raw extracted content."""
    if not text:
        return ""

    # 1. Remove null bytes
    cleaned = _NULL_BYTES_RE.sub("", text)

    # 2. Unicode NFKC normalization
    cleaned = unicodedata.normalize("NFKC", cleaned)

    # 3. Unify line endings to LF
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

    # 4. Replace tabs with 4 spaces for consistent column alignment
    cleaned = _TABS_RE.sub("    ", cleaned)

    # 5. Remove trailing spaces on lines
    cleaned = _TRAILING_SPACES_RE.sub("\n", cleaned)

    # 6. Filter out pure page header lines (e.g. "Page 1 of 12")
    lines = []
    for line in cleaned.splitlines():
        if _PAGE_NUMBER_HEADER_RE.match(line):
            continue
        lines.append(line.rstrip())

    cleaned = "\n".join(lines)

    # 7. Consolidate 3+ consecutive blank lines down to 2
    cleaned = _MULTIPLE_NEWLINES_RE.sub("\n\n", cleaned)

    return cleaned.strip()
