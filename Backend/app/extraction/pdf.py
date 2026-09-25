"""PDF Extraction Module (Phase 3).

Extracts:
- Page-by-page text with explicit page numbers
- Document metadata (Title, Author, Creator, Page Count)
- Embedded images if available
- Tables detected from text alignment
Uses pypdf as primary extractor with PyMuPDF fallback for complex encodings.
"""
from __future__ import annotations

import io
import logging
import re
from typing import Any, Dict, List, Tuple

from ..core.exceptions import ExtractionError
from .normalizer import normalize_text
from .schemas import ExtractedDocument, ExtractedImageMeta, ExtractedPage, ExtractedTable

log = logging.getLogger("extraction.pdf")

_WS_TABLE_RE = re.compile(r"[ \t]{3,}|\|")


def extract_pdf_document(
    file_bytes: bytes,
    filename: str,
    document_id: str,
    mime_type: str = "application/pdf",
    uid: str = "",
    project_id: str = "",
    source_id: str = "",
    persist_images: bool = False,
) -> ExtractedDocument:
    """Extract PDF pages, text, metadata, and optional images."""
    if not file_bytes:
        raise ExtractionError("PDF file payload is empty.")

    pages: List[ExtractedPage] = []
    images: List[ExtractedImageMeta] = []
    tables: List[ExtractedTable] = []
    metadata: Dict[str, Any] = {}

    # Primary: pypdf
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(file_bytes))
        meta = reader.metadata
        if meta:
            metadata = {
                "title": str(getattr(meta, "title", "") or ""),
                "author": str(getattr(meta, "author", "") or ""),
                "creator": str(getattr(meta, "creator", "") or ""),
                "producer": str(getattr(meta, "producer", "") or ""),
                "pageCount": len(reader.pages),
            }
        else:
            metadata = {"pageCount": len(reader.pages)}

        for idx, page in enumerate(reader.pages):
            try:
                raw_text = page.extract_text() or ""
            except Exception as page_err:
                log.warning("pypdf page %d extraction warning: %s", idx + 1, page_err)
                raw_text = ""

            norm_page_text = normalize_text(raw_text)
            words = len(norm_page_text.split()) if norm_page_text else 0
            pages.append(
                ExtractedPage(
                    pageNumber=idx + 1,
                    text=norm_page_text,
                    characterCount=len(norm_page_text),
                    wordCount=words,
                )
            )

            if persist_images and uid and project_id and source_id:
                try:
                    for img_idx, img in enumerate(page.images):
                        raw_img = img.data
                        from ..storage.service import save_extracted_image

                        img_id, key = save_extracted_image(
                            uid=uid,
                            project_id=project_id,
                            source_id=source_id,
                            image_bytes=raw_img,
                        )
                        images.append(
                            ExtractedImageMeta(
                                imageId=img_id,
                                filename=img.name or f"{img_id}.png",
                                path=key,
                                pageNumber=idx + 1,
                            )
                        )
                except Exception as img_err:
                    log.debug("PDF image extraction warning (p%d): %s", idx + 1, img_err)

    except Exception as exc:
        log.warning("pypdf failed for %s: %s. Trying PyMuPDF fallback.", filename, exc)

    # Fallback: PyMuPDF if pypdf yielded no text
    full_text = "\n\n".join(p.text for p in pages if p.text).strip()
    if not full_text:
        try:
            import pymupdf

            with pymupdf.open(stream=file_bytes, filetype="pdf") as doc:
                pages.clear()
                metadata["pageCount"] = len(doc)
                for idx, page in enumerate(doc):
                    t = normalize_text(page.get_text("text"))
                    words = len(t.split()) if t else 0
                    pages.append(
                        ExtractedPage(
                            pageNumber=idx + 1,
                            text=t,
                            characterCount=len(t),
                            wordCount=words,
                        )
                    )
                full_text = "\n\n".join(p.text for p in pages if p.text).strip()
        except Exception as mu_err:
            log.warning("PyMuPDF fallback failed: %s", mu_err)

    if not pages and not full_text:
        raise ExtractionError(f"Could not extract any text or pages from PDF '{filename}'. File may be corrupt or encrypted.")

    # Detect heuristic tables from page text
    for p in pages:
        if not p.text:
            continue
        rows = [ln for ln in p.text.splitlines() if _WS_TABLE_RE.search(ln)]
        if len(rows) >= 2:
            parsed_rows = [[c.strip() for c in re.split(r"\s{3,}|\||\t", r) if c.strip()] for r in rows[:50]]
            if parsed_rows:
                tables.append(
                    ExtractedTable(
                        tableId=f"TBL-p{p.pageNumber:02d}-1",
                        pageNumber=p.pageNumber,
                        rows=parsed_rows,
                        source="pdf_heuristic",
                    )
                )

    metadata["characterCount"] = len(full_text)
    metadata["wordCount"] = len(full_text.split()) if full_text else 0

    return ExtractedDocument(
        documentId=document_id,
        filename=filename,
        fileType="pdf",
        mimeType=mime_type,
        sizeBytes=len(file_bytes),
        metadata=metadata,
        content=full_text,
        pages=pages,
        sections=[],
        tables=tables,
        images=images,
        extractionStatus="completed",
    )
