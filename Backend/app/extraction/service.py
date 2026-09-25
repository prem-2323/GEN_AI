"""Extraction Service Orchestrator (Phase 3).

Delegates extraction to specialized format handlers:
- pdf.py   -> PDF text, pages, metadata, images
- docx.py  -> DOCX headings, paragraphs, sections, tables
- txt.py   -> TXT/MD text encodings, lines, tables

Produces the canonical ExtractedDocument model between Phase 3 Ingestion and Phase 4 DocLink.
"""
from __future__ import annotations

import io
import logging
from typing import Any, Dict, List, Optional

from ..core.exceptions import ExtractionError
from ..core.logging import get_logger
from .docx import extract_docx_document
from .normalizer import normalize_text
from .pdf import extract_pdf_document
from .schemas import ExtractedDocument
from .txt import extract_txt_document


log = get_logger("extraction.service")


class ExtractionService:
    """Core extraction engine for multi-format documents."""

    @classmethod
    def extract_document(
        cls,
        file_bytes: bytes,
        filename: str,
        document_id: str,
        mime_type: str = "",
        ext: str = "",
        uid: str = "",
        project_id: str = "",
        source_id: str = "",
        persist_images: bool = False,
    ) -> ExtractedDocument:
        """Main Phase 3 extraction pipeline entrypoint returning ExtractedDocument model."""
        if not file_bytes:
            raise ExtractionError(f"Cannot extract empty file '{filename}' (0 bytes).")

        resolved_ext = (ext or filename.rsplit(".", 1)[-1]).lower().lstrip(".")
        log.info("EXTRACTION_STARTED doc_id=%s filename=%s ext=%s size=%d", document_id, filename, resolved_ext, len(file_bytes))

        try:
            if resolved_ext == "pdf":
                doc = extract_pdf_document(
                    file_bytes=file_bytes,
                    filename=filename,
                    document_id=document_id,
                    mime_type=mime_type or "application/pdf",
                    uid=uid,
                    project_id=project_id,
                    source_id=source_id,
                    persist_images=persist_images,
                )
            elif resolved_ext == "docx":
                doc = extract_docx_document(
                    file_bytes=file_bytes,
                    filename=filename,
                    document_id=document_id,
                    mime_type=mime_type or "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            elif resolved_ext in ("txt", "md"):
                doc = extract_txt_document(
                    file_bytes=file_bytes,
                    filename=filename,
                    document_id=document_id,
                    mime_type=mime_type or "text/plain",
                    kind=resolved_ext,
                )
            else:
                # Fallback textlike extraction
                doc = extract_txt_document(
                    file_bytes=file_bytes,
                    filename=filename,
                    document_id=document_id,
                    mime_type=mime_type or "application/octet-stream",
                    kind=resolved_ext or "bin",
                )

            log.info("EXTRACTION_COMPLETED doc_id=%s status=%s pages=%d chars=%d", document_id, doc.extractionStatus, len(doc.pages), len(doc.content))
            return doc
        except ExtractionError:
            log.error("EXTRACTION_FAILED doc_id=%s filename=%s", document_id, filename)
            raise
        except Exception as exc:
            log.error("EXTRACTION_FAILED doc_id=%s filename=%s error=%s", document_id, filename, exc)
            raise ExtractionError(f"Failed to extract document '{filename}': {exc}") from exc

    @classmethod
    def extract_normalized(
        cls,
        file_bytes: bytes,
        filename: str,
        ext: str,
        uid: str = "",
        project_id: str = "",
        source_id: str = "",
        persist_images: bool = False,
    ) -> Dict[str, Any]:
        """Backward compatible normalized dictionary adapter."""
        doc = cls.extract_document(
            file_bytes=file_bytes,
            filename=filename,
            document_id=source_id or "src_temp",
            ext=ext,
            uid=uid,
            project_id=project_id,
            source_id=source_id,
            persist_images=persist_images,
        )

        # Convert ExtractedDocument into legacy dictionary shape expected by Phase 4/5
        return {
            "sourceId": doc.documentId,
            "document": {"name": doc.filename, "type": doc.fileType},
            "text": {"content": doc.content, "characterCount": len(doc.content)},
            "pages": [p.model_dump(by_alias=True) for p in doc.pages],
            "sections": [s.model_dump(by_alias=True) for s in doc.sections],
            "tables": [t.model_dump(by_alias=True) for t in doc.tables],
            "images": [i.model_dump(by_alias=True) for i in doc.images],
            "metadata": doc.metadata,
        }

    @classmethod
    def extract_content(
        cls, file_bytes: bytes, filename: str, mime_type: str = "", **kwargs: Any
    ) -> Dict[str, Any]:
        """Lightweight extraction shape adapter."""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"
        doc = cls.extract_document(
            file_bytes=file_bytes,
            filename=filename,
            document_id="src_standalone",
            mime_type=mime_type,
            ext=ext,
        )
        label = {"pdf": "PDF", "docx": "DOCX", "md": "TEXT"}.get(ext, ext.upper() if ext else "TEXT")
        return {
            "name": filename,
            "type": label,
            "size": f"{len(file_bytes) / 1024:.1f} KB",
            "extractedText": doc.content,
            "status": "ready",
            "pageCount": len(doc.pages),
            "imageCount": len(doc.images),
            "tableCount": len(doc.tables),
        }


# Module level helper aliases
extract_document = ExtractionService.extract_document
extract_normalized = ExtractionService.extract_normalized
extract_content = ExtractionService.extract_content
extract_pdf = extract_pdf_document
extract_docx = extract_docx_document
extract_textlike = extract_txt_document
extract_image = extract_txt_document
