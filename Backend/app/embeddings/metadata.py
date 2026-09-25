"""Phase 6 Metadata & Provenance Helpers."""
from __future__ import annotations

import hashlib
from typing import Any, Dict, Optional

from .models import ChunkMetadata, SemanticChunk


def compute_content_hash(text: str) -> str:
    """Compute SHA-256 content hash of chunk text for caching & idempotency."""
    cleaned = (text or "").strip().encode("utf-8")
    return hashlib.sha256(cleaned).hexdigest()


def generate_deterministic_chunk_id(document_id: str, chunk_index: int, content_hash: str) -> str:
    """Generate deterministic chunk ID to prevent duplicate vectors on re-indexing."""
    short_hash = content_hash[:8]
    return f"{document_id}_chunk_{chunk_index:03d}_{short_hash}"


def build_chunk_metadata(
    chunk: SemanticChunk,
    source_filename: str = "",
    document_type: str = "document",
) -> ChunkMetadata:
    """Build ChunkMetadata from SemanticChunk."""
    return ChunkMetadata(
        chunk_id=chunk.chunk_id,
        document_id=chunk.document_id,
        section=chunk.section,
        page_start=chunk.page_start,
        page_end=chunk.page_end,
        chunk_index=chunk.chunk_index,
        source_filename=source_filename or chunk.document_id,
        document_type=document_type,
        character_count=chunk.char_count,
        token_count=chunk.token_count,
        content_hash=chunk.content_hash,
        created_at=chunk.created_at,
    )


__all__ = [
    "compute_content_hash",
    "generate_deterministic_chunk_id",
    "build_chunk_metadata",
]
