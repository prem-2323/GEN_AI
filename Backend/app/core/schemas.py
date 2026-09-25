"""Shared core Pydantic schemas and standard request/response models."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard unified API response wrapper."""
    ok: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    error: Optional[str] = None


class HealthStatus(BaseModel):
    """Health check response schema."""
    status: str = "ok"
    app_name: str
    environment: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginationParams(BaseModel):
    """Pagination query parameters."""
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class DocumentMetadata(BaseModel):
    """Normalized document metadata schema."""
    originalName: str
    storedName: str
    mimeType: str
    size: int
    storagePath: str
    fileId: Optional[str] = None
    sha256: Optional[str] = None
    pageCount: Optional[int] = None
    characterCount: Optional[int] = None
    title: Optional[str] = None
    author: Optional[str] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)


class Document(BaseModel):
    """Core document domain entity."""
    documentId: str
    projectId: str
    userId: str
    metadata: DocumentMetadata
    stage: str = "uploaded"
    progress: int = 0
    error: Optional[str] = None


class ExtractionResult(BaseModel):
    """Normalized extraction result shape."""
    sourceId: str
    document: Dict[str, Any]
    text: Dict[str, Any]
    pages: List[Dict[str, Any]] = Field(default_factory=list)
    images: List[Dict[str, Any]] = Field(default_factory=list)
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProcessingRequest(BaseModel):
    """Generic document processing request."""
    projectId: str
    sourceId: Optional[str] = None
    pipelineSteps: List[str] = Field(default_factory=lambda: ["extract", "analyze", "uckr", "transform"])
    options: Dict[str, Any] = Field(default_factory=dict)


class ProcessingResponse(BaseModel):
    """Generic document processing pipeline response."""
    ok: bool = True
    projectId: str
    sourceId: Optional[str] = None
    jobId: Optional[str] = None
    stage: str
    progress: int = 100
    results: Dict[str, Any] = Field(default_factory=dict)
