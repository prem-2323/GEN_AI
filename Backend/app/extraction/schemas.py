"""Schemas for Document Extraction (Phase 3).

Defines the standard ExtractedDocument handoff object passed from Phase 3 to Phase 4.
"""
from __future__ import annotations

from dataclasses import field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExtractedPage(BaseModel):
    """Represents a single page or chunk extracted from a document."""
    pageNumber: int = Field(..., alias="pageNumber")
    text: str = ""
    characterCount: int = 0
    wordCount: int = 0


class ExtractedSection(BaseModel):
    """Represents a section or heading chunk extracted from structured documents."""
    heading: str = ""
    level: int = 1
    content: str = ""


class ExtractedTable(BaseModel):
    """Represents a table extracted from DOCX, PDF, or Markdown."""
    tableId: str = ""
    pageNumber: int = 1
    rows: List[List[str]] = Field(default_factory=list)
    source: str = "extracted"


class ExtractedImageMeta(BaseModel):
    """Metadata for images embedded or extracted from documents."""
    imageId: str = ""
    filename: str = ""
    path: str = ""
    pageNumber: int = 0
    width: Optional[int] = None
    height: Optional[int] = None
    format: str = ""


class ExtractedDocument(BaseModel):
    """Canonical extracted document model between Ingestion (Phase 3) and DocLink (Phase 4)."""
    documentId: str = Field(..., alias="documentId")
    filename: str
    fileType: str = Field(..., alias="fileType")  # pdf, docx, txt, md, image
    mimeType: str = Field(default="", alias="mimeType")
    sizeBytes: int = Field(default=0, alias="sizeBytes")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    content: str = ""  # Full normalized plain text content
    pages: List[ExtractedPage] = Field(default_factory=list)
    sections: List[ExtractedSection] = Field(default_factory=list)
    tables: List[ExtractedTable] = Field(default_factory=list)
    images: List[ExtractedImageMeta] = Field(default_factory=list)
    extractionStatus: str = Field(default="completed", alias="extractionStatus")  # completed, failed, partial
    error: Optional[str] = None
    createdAt: str = Field(default_factory=utcnow_iso, alias="createdAt")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
