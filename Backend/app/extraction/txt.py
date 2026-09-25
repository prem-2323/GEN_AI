"""TXT and Markdown Extraction Module (Phase 3).

Supports plain text (.txt) and Markdown (.md) documents with automatic encoding detection:
- UTF-8 with fallback to Latin-1/CP1252
- Text normalization
- Line and word statistics
- Heuristic table detection
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

from ..core.exceptions import ExtractionError
from .normalizer import normalize_text
from .schemas import ExtractedDocument, ExtractedPage, ExtractedTable

log = logging.getLogger("extraction.txt")

_WS_TABLE_RE = re.compile(r"[ \t]{3,}|\|")


def _decode_bytes(file_bytes: bytes) -> str:
    """Safely decode bytes trying utf-8, chardet, and fallback encodings."""
    if not file_bytes:
        return ""

    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            return file_bytes.decode(enc)
        except (UnicodeDecodeError, ValueError):
            continue

    return file_bytes.decode("utf-8", errors="ignore")


def extract_txt_document(
    file_bytes: bytes,
    filename: str,
    document_id: str,
    mime_type: str = "text/plain",
    kind: str = "txt",
) -> ExtractedDocument:
    """Extract text from TXT or MD files."""
    if not file_bytes:
        raise ExtractionError("Text file payload is empty.")

    raw_text = _decode_bytes(file_bytes)
    full_text = normalize_text(raw_text)

    if not full_text:
        log.warning("Extracted text for '%s' is empty after normalization.", filename)

    lines = full_text.splitlines()
    word_count = len(full_text.split()) if full_text else 0

    # Chunk into estimated pages (~2000 chars per page)
    pages: List[ExtractedPage] = []
    chunk_size = 2000
    for i in range(0, max(1, len(full_text)), chunk_size):
        chunk = full_text[i : i + chunk_size]
        pages.append(
            ExtractedPage(
                pageNumber=len(pages) + 1,
                text=chunk,
                characterCount=len(chunk),
                wordCount=len(chunk.split()) if chunk else 0,
            )
        )

    # Detect heuristic tables
    tables: List[ExtractedTable] = []
    for p in pages:
        t_rows = [ln for ln in p.text.splitlines() if _WS_TABLE_RE.search(ln)]
        if len(t_rows) >= 2:
            parsed = [[c.strip() for c in re.split(r"\s{3,}|\||\t", r) if c.strip()] for r in t_rows[:50]]
            if parsed:
                tables.append(
                    ExtractedTable(
                        tableId=f"TBL-p{p.pageNumber:02d}-1",
                        pageNumber=p.pageNumber,
                        rows=parsed,
                        source=f"{kind}_heuristic",
                    )
                )

    metadata: Dict[str, Any] = {
        "lineCount": len(lines),
        "characterCount": len(full_text),
        "wordCount": word_count,
        "pageCount": len(pages),
    }

    return ExtractedDocument(
        documentId=document_id,
        filename=filename,
        fileType=kind,
        mimeType=mime_type,
        sizeBytes=len(file_bytes),
        metadata=metadata,
        content=full_text,
        pages=pages,
        sections=[],
        tables=tables,
        images=[],
        extractionStatus="completed",
    )
