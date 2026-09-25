"""Phase 6 Vector Store Implementation.

Provides fast cosine-similarity vector search, top-k retrieval, metadata filtering,
idempotent upserts, document-level vector deletion, and file persistence.
"""
from __future__ import annotations

import copy
import json
import math
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..core.config import get_settings
from .interface import VectorStoreInterface
from .models import ChunkMetadata, SearchResult, VectorRecord

log = logging.getLogger("gen-transform.embeddings.vector_store")


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculate cosine similarity score between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 <= 1e-9 or norm2 <= 1e-9:
        return 0.0
    return max(0.0, min(1.0, dot / (norm1 * norm2)))


class MemoryVectorStore(VectorStoreInterface):
    """In-memory Vector Store with optional local JSON persistence."""

    def __init__(self, persistence_file: Optional[str] = None) -> None:
        settings = get_settings()
        if persistence_file:
            self.file_path = Path(persistence_file)
        else:
            self.file_path = Path(settings.storage_root) / "data" / "vector_store.json"

        self._records: Dict[str, VectorRecord] = {}
        self._load()

    def _load(self) -> None:
        """Load persisted vectors from file if available."""
        if self.file_path.exists() and self.file_path.is_file():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                    for item in raw_data:
                        rec = VectorRecord(**item)
                        self._records[rec.id] = rec
                log.info("Loaded %d vectors from %s", len(self._records), self.file_path.name)
            except Exception as exc:
                log.warning("Failed to load vector store from %s: %s", self.file_path, exc)
                self._records = {}

    def _save(self) -> None:
        """Save vector records to disk."""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            temp_file = self.file_path.with_suffix(".tmp")
            data = [rec.model_dump() for rec in self._records.values()]
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            temp_file.replace(self.file_path)
        except Exception as exc:
            log.error("Failed to save vector store to %s: %s", self.file_path, exc)

    def add_vectors(
        self,
        ids: List[str],
        vectors: List[List[float]],
        metadata: List[Dict[str, Any]],
    ) -> bool:
        """Add or update vectors in vector store (Idempotent upsert)."""
        if len(ids) != len(vectors) or len(ids) != len(metadata):
            raise ValueError("Mismatched list lengths for ids, vectors, and metadata.")

        for vid, vec, meta in zip(ids, vectors, metadata):
            chunk_meta = ChunkMetadata(**meta) if not isinstance(meta, ChunkMetadata) else meta
            rec = VectorRecord(
                id=vid,
                vector=vec,
                text=meta.get("text", "") if isinstance(meta, dict) else "",
                metadata=chunk_meta,
            )
            self._records[vid] = rec

        self._save()
        return True

    def add_records(self, records: List[VectorRecord]) -> bool:
        """Batch insert typed VectorRecord instances."""
        for rec in records:
            self._records[rec.id] = rec
        self._save()
        return True

    def similarity_search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Perform top-K cosine similarity search over vector store with optional metadata filtering."""
        if not self._records or not query_vector:
            return []

        scored_results: List[Tuple[float, VectorRecord]] = []

        for rec in self._records.values():
            meta_dict = rec.metadata.model_dump()

            # Metadata filtering check
            if filter_dict:
                match = True
                for k, v in filter_dict.items():
                    if v is not None and meta_dict.get(k) != v:
                        match = False
                        break
                if not match:
                    continue

            score = cosine_similarity(query_vector, rec.vector)
            scored_results.append((score, rec))

        # Sort by similarity score descending
        scored_results.sort(key=lambda item: item[0], reverse=True)

        results: List[SearchResult] = []
        for score, rec in scored_results[:top_k]:
            results.append(
                SearchResult(
                    chunk_id=rec.id,
                    score=round(score, 4),
                    text=rec.text or rec.metadata.source_filename,
                    document_id=rec.metadata.document_id,
                    page=rec.metadata.page_start,
                    section=rec.metadata.section,
                    source_filename=rec.metadata.source_filename,
                    metadata=rec.metadata.model_dump(),
                )
            )

        return results

    def delete_vectors(self, ids: List[str]) -> bool:
        """Remove specific vector IDs from vector store."""
        removed = 0
        for vid in ids:
            if vid in self._records:
                del self._records[vid]
                removed += 1
        if removed > 0:
            self._save()
        return True

    def delete_document_vectors(self, document_id: str) -> int:
        """Delete all vectors belonging to document_id."""
        to_remove = [vid for vid, rec in self._records.items() if rec.metadata.document_id == document_id]
        for vid in to_remove:
            del self._records[vid]
        if to_remove:
            self._save()
        log.info("Deleted %d vectors for document_id '%s'", len(to_remove), document_id)
        return len(to_remove)

    def get_by_id(self, chunk_id: str) -> Optional[VectorRecord]:
        """Retrieve single VectorRecord by chunk_id."""
        return copy.deepcopy(self._records.get(chunk_id))

    def get_document_vectors(self, document_id: str) -> List[VectorRecord]:
        """Retrieve all VectorRecords for a specific document_id."""
        return [copy.deepcopy(rec) for rec in self._records.values() if rec.metadata.document_id == document_id]

    def clear(self) -> None:
        """Empty vector store."""
        self._records.clear()
        self._save()


__all__ = ["MemoryVectorStore", "cosine_similarity"]
