"""Phase 6 Embedding & Vector Store Models."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from ..utils.helpers import utcnow_iso


class SemanticChunk(BaseModel):
    """A semantically coherent chunk of document text preserving section boundaries."""
    chunk_id: str
    document_id: str
    text: str
    section: str = "Main"
    page_start: int = 1
    page_end: int = 1
    chunk_index: int = 0
    char_count: int = 0
    token_count: int = 0
    content_hash: str = ""
    created_at: str = Field(default_factory=utcnow_iso)

    model_config = {"extra": "allow"}


class ChunkMetadata(BaseModel):
    """Provenance and metadata attached to every vector record."""
    chunk_id: str
    document_id: str
    section: str = "Main"
    page_start: int = 1
    page_end: int = 1
    chunk_index: int = 0
    source_filename: str = ""
    document_type: str = "document"
    character_count: int = 0
    token_count: int = 0
    content_hash: str = ""
    created_at: str = Field(default_factory=utcnow_iso)

    model_config = {"extra": "allow"}


class VectorRecord(BaseModel):
    """Vector entry stored in Vector Store."""
    id: str  # chunk_id
    vector: List[float]
    text: str = ""
    metadata: ChunkMetadata

    model_config = {"extra": "allow"}


class SearchResult(BaseModel):
    """Result item returned by semantic similarity search."""
    chunk_id: str
    score: float
    text: str
    document_id: str
    page: int = 1
    section: str = "Main"
    source_filename: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "allow"}


class SearchRequest(BaseModel):
    """Request contract for semantic search endpoint."""
    query: str
    top_k: int = 5
    document_id: Optional[str] = None
    section: Optional[str] = None
    min_score: float = 0.0

    model_config = {"extra": "allow"}


class IndexDocumentResponse(BaseModel):
    """Response contract for document indexing endpoint."""
    ok: bool = True
    document_id: str
    status: str = "indexed"
    total_chunks: int = 0
    embedding_time_ms: float = 0.0
    index_time_ms: float = 0.0
    created_at: str = Field(default_factory=utcnow_iso)

    model_config = {"extra": "allow"}


class IndexingMetrics(BaseModel):
    """Performance metrics for document chunking, embedding, and vector storage."""
    document_id: str
    chunks_count: int = 0
    extraction_time_ms: float = 0.0
    chunking_time_ms: float = 0.0
    embedding_time_ms: float = 0.0
    index_time_ms: float = 0.0
    total_latency_ms: float = 0.0
    created_at: str = Field(default_factory=utcnow_iso)

    model_config = {"extra": "allow"}


class EmbeddingProvider:
    DETERMINISTIC = "deterministic"
    OLLAMA = "ollama"
    GEMINI = "gemini"


__all__ = [
    "SemanticChunk",
    "ChunkMetadata",
    "VectorRecord",
    "SearchResult",
    "SearchRequest",
    "IndexDocumentResponse",
    "IndexingMetrics",
    "EmbeddingProvider",
]
