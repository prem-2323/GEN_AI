"""Schemas for Ingestion Layer (Phase 3)."""
from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class IngestionResponse(BaseModel):
    """Response returned by document upload API."""
    ok: bool = True
    documentId: str = Field(..., alias="documentId")
    filename: str
    fileType: str = Field(..., alias="fileType")
    mimeType: str = Field(..., alias="mimeType")
    sizeBytes: int = Field(..., alias="sizeBytes")
    status: str = "processed"
    extractionStatus: str = Field("completed", alias="extractionStatus")
    storagePath: str = Field("", alias="storagePath")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

    model_config = {
        "populate_by_name": True,
    }
