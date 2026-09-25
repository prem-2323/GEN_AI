"""Document content extraction module supporting PDF, DOCX, TXT, MD, and Images."""
from __future__ import annotations

import io
import re
from typing import Any, Dict, List, Optional

from ..core.exceptions import ExtractionError
from ..core.logging import get_logger

log = get_logger("extraction.service")

_WS_TABLE_RE = re.compile(r"[ \t]{3,}|\|")


class ExtractionService:
    """Core extraction engine for multi-format documents."""

    @staticmethod
    def chunk_pages(text: str, per_page: int = 2500) -> List[Dict[str, Any]]:
        """Split plain text into estimated page chunks."""
        pages = []
        for i in range(0, max(1, len(text)), per_page):
            pages.append({"pageNumber": len(pages) + 1, "text": text[i : i + per_page]})
        return pages

    @staticmethod
    def heuristic_tables(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect markdown / whitespace delimited tables from page text."""
        tables = []
        for p in pages:
            rows = [ln for ln in p["text"].splitlines() if _WS_TABLE_RE.search(ln)]
            if len(rows) >= 2:
                tables.append({
                    "tableId": f"TBL-{p['pageNumber']:03d}-H1",
                    "pageNumber": p["pageNumber"],
                    "rows": [[c.strip() for c in re.split(r"\s{3,}|\||\t", r) if c.strip()] for r in rows[:50]],
                    "source": "heuristic",
                })
        return tables

    @staticmethod
    def get_image_info(image_bytes: bytes) -> Dict[str, Any]:
        """Extract dimension and format metadata from image bytes."""
        try:
            from PIL import Image

            with Image.open(io.BytesIO(image_bytes)) as im:
                return {"width": im.width, "height": im.height, "format": (im.format or "").lower()}
        except Exception:
            return {}

    @classmethod
    def extract_pdf(
        cls,
        file_bytes: bytes,
        filename: str,
        uid: str = "",
        project_id: str = "",
        source_id: str = "",
        persist_images: bool = False,
    ) -> Dict[str, Any]:
        """Extract text, tables, and images from PDF documents using pypdf and PyMuPDF fallback."""
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(file_bytes))
        pages: List[Dict[str, Any]] = []
        images: List[Dict[str, Any]] = []
        for idx, page in enumerate(reader.pages):
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""
            pages.append({"pageNumber": idx + 1, "text": text.strip()})
            if persist_images:
                try:
                    for img in page.images:
                        try:
                            raw = img.data
                        except Exception:
                            continue
                        from ..services.storage import storage_service as store

                        rel = store.save_extracted_image(uid, project_id, source_id, raw)
                        images.append({
                            "imageId": f"IMG-{idx + 1:03d}-{len(images) + 1:02d}",
                            "path": rel,
                            "pageNumber": idx + 1,
                            **cls.get_image_info(raw),
                        })
                except Exception as exc:
                    log.debug("pdf image extraction skipped (p%d): %s", idx + 1, exc)

        full = "\n\n".join(p["text"] for p in pages).strip()

        # PyMuPDF fallback for complex or scanned text encodings
        if not full:
            try:
                import pymupdf

                with pymupdf.open(stream=file_bytes, filetype="pdf") as doc:
                    mu_pages = []
                    for idx, page in enumerate(doc):
                        t = page.get_text("text").strip()
                        mu_pages.append({"pageNumber": idx + 1, "text": t})
                    mu_full = "\n\n".join(p["text"] for p in mu_pages).strip()
                    if mu_full:
                        pages = mu_pages
                        full = mu_full
            except Exception as mu_err:
                log.debug("PyMuPDF fallback skipped: %s", mu_err)

        meta = reader.metadata
        return {
            "document": {"name": filename, "type": "pdf"},
            "text": {"content": full, "characterCount": len(full)},
            "pages": pages,
            "images": images,
            "tables": cls.heuristic_tables(pages),
            "metadata": {
                "pageCount": len(pages),
                "title": str(getattr(meta, "title", "") or ""),
                "author": str(getattr(meta, "author", "") or ""),
            },
        }

    @classmethod
    def extract_docx(cls, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Extract text, tables, and metadata from DOCX documents."""
        from docx import Document

        doc = Document(io.BytesIO(file_bytes))
        paras = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
        full = "\n".join(paras).strip()
        pages = cls.chunk_pages(full)
        tables = []
        for ti, t in enumerate(doc.tables):
            rows = [[c.text.strip() for c in row.cells] for row in t.rows]
            if rows:
                tables.append({"tableId": f"TBL-{ti + 1:03d}", "pageNumber": 1, "rows": rows, "source": "docx"})
        if not tables:
            tables = cls.heuristic_tables(pages)
        core = doc.core_properties
        return {
            "document": {"name": filename, "type": "docx"},
            "text": {"content": full, "characterCount": len(full)},
            "pages": pages,
            "images": [],
            "tables": tables,
            "metadata": {
                "paragraphs": len(paras),
                "tables": len(doc.tables),
                "title": core.title or "",
                "author": core.author or "",
            },
        }

    @classmethod
    def extract_textlike(cls, file_bytes: bytes, filename: str, kind: str) -> Dict[str, Any]:
        """Extract plain text or Markdown files."""
        text = file_bytes.decode("utf-8", errors="ignore").strip()
        pages = cls.chunk_pages(text)
        return {
            "document": {"name": filename, "type": kind},
            "text": {"content": text, "characterCount": len(text)},
            "pages": pages,
            "images": [],
            "tables": cls.heuristic_tables(pages),
            "metadata": {"lines": len(text.splitlines())},
        }

    @classmethod
    def extract_image(cls, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Extract visual metadata from image files."""
        info = cls.get_image_info(file_bytes)
        return {
            "document": {"name": filename, "type": "image"},
            "text": {"content": "", "characterCount": 0},
            "pages": [],
            "images": [{"imageId": "IMG-001-01", "path": "", "pageNumber": 0, **info}],
            "tables": [],
            "metadata": {"visualOnly": True, **info},
        }

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
        """Full normalized extraction for any supported file extension."""
        ext = ext.lower()
        if ext == "pdf":
            result = cls.extract_pdf(file_bytes, filename, uid, project_id, source_id, persist_images)
        elif ext == "docx":
            result = cls.extract_docx(file_bytes, filename)
        elif ext in ("txt", "md"):
            result = cls.extract_textlike(file_bytes, filename, ext)
        elif ext in ("png", "jpg", "jpeg"):
            result = cls.extract_image(file_bytes, filename)
        else:
            raise ExtractionError(f"Unsupported file extension: {ext}")
        result["sourceId"] = source_id or "SRC-pending"
        return result

    @classmethod
    def extract_content(
        cls, file_bytes: bytes, filename: str, mime_type: str = "", **kwargs: Any
    ) -> Dict[str, Any]:
        """Legacy lightweight extraction shape for backward compatibility."""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"
        try:
            norm = cls.extract_normalized(file_bytes, filename, ext)
            text = norm["text"]["content"]
        except Exception:
            text = file_bytes.decode("utf-8", errors="ignore").strip()
            norm = {"pages": [], "images": [], "tables": []}
        label = {"pdf": "PDF", "docx": "DOCX", "md": "TEXT"}.get(ext, ext.upper() if ext else "TEXT")
        return {
            "name": filename,
            "type": label,
            "size": f"{len(file_bytes) / 1024:.1f} KB",
            "extractedText": text,
            "status": "ready",
            "pageCount": len(norm.get("pages", [])),
            "imageCount": len(norm.get("images", [])),
            "tableCount": len(norm.get("tables", [])),
        }


# Convenience module-level aliases
extract_normalized = ExtractionService.extract_normalized
extract_content = ExtractionService.extract_content
extract_pdf = ExtractionService.extract_pdf
extract_docx = ExtractionService.extract_docx
extract_textlike = ExtractionService.extract_textlike
extract_image = ExtractionService.extract_image
