"""Source file model."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class SourceFileModel(BaseModel):
    id: str
    name: str
    type: str  # PDF, DOCX, TXT, IMAGE, VIDEO, TEXT
    size: str = "0 KB"
    pages: Optional[int] = None
    extractedText: str = ""
    status: str = "ready"
    uploadedAt: str = ""
