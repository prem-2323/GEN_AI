"""Export system data schemas, MIME types, and governance definitions (Phase 10)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

MIME_TYPES: Dict[str, str] = {
    "txt": "text/plain",
    "md": "text/markdown",
    "json": "application/json",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "mp3": "audio/mpeg",
    "mp4": "video/mp4",
}

DEFAULT_EXTENSIONS: Dict[str, str] = {
    "text/plain": "txt",
    "text/markdown": "md",
    "application/json": "json",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    "audio/mpeg": "mp3",
    "video/mp4": "mp4",
}


class ExportRequest(BaseModel):
    format: str = Field("docx", description="Target export format: txt, docx, pdf, pptx, mp3, json, md")
    require_approval: bool = Field(False, description="Enforce that deliverable must be approved before export")
    custom_title: Optional[str] = Field(None, description="Optional override title for the exported document")


class ExportRecord(BaseModel):
    exportId: str
    userId: str
    projectId: str
    sourceId: Optional[str] = None
    deliverableId: str
    uckrId: Optional[str] = None
    uckrVersion: int = 1
    exportType: str
    filename: str
    mimeType: str
    fileId: str
    fileSize: int
    status: str = "completed"
    storagePath: Optional[str] = None
    createdAt: str
    updatedAt: Optional[str] = None
