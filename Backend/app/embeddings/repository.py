"""Phase 6 Vector Store Repository & Factory."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union

from .interface import VectorStoreInterface
from .models import SearchResult, VectorRecord
from .vector_store import MemoryVectorStore

log = logging.getLogger("gen-transform.embeddings.repository")


class VectorStoreRepository(VectorStoreInterface):
    """Production Repository adapter delegating to underlying Vector Store implementation."""

    def __init__(self, store: Optional[VectorStoreInterface] = None) -> None:
        self.store = store or MemoryVectorStore()

    def add_vectors(
        self,
        ids: List[str],
        vectors: List[List[float]],
        metadata: List[Dict[str, Any]],
    ) -> bool:
        return self.store.add_vectors(ids, vectors, metadata)

    def similarity_search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        return self.store.similarity_search(query_vector, top_k=top_k, filter_dict=filter_dict)

    def delete_vectors(self, ids: List[str]) -> bool:
        if hasattr(self.store, "delete_vectors"):
            return self.store.delete_vectors(ids)
        return True

    def delete_document_vectors(self, document_id: str) -> int:
        if hasattr(self.store, "delete_document_vectors"):
            return self.store.delete_document_vectors(document_id)
        return 0

    def get_by_id(self, chunk_id: str) -> Optional[VectorRecord]:
        if hasattr(self.store, "get_by_id"):
            return self.store.get_by_id(chunk_id)
        return None

    def get_document_vectors(self, document_id: str) -> List[VectorRecord]:
        if hasattr(self.store, "get_document_vectors"):
            return self.store.get_document_vectors(document_id)
        return []


VectorStoreBoundaryRepository = VectorStoreRepository
_GLOBAL_VECTOR_STORE: Optional[MemoryVectorStore] = None


def get_vector_store() -> MemoryVectorStore:
    """Get singleton VectorStore instance."""
    global _GLOBAL_VECTOR_STORE
    if _GLOBAL_VECTOR_STORE is None:
        _GLOBAL_VECTOR_STORE = MemoryVectorStore()
    return _GLOBAL_VECTOR_STORE


def set_vector_store(store: MemoryVectorStore) -> None:
    """Inject vector store instance for testing."""
    global _GLOBAL_VECTOR_STORE
    _GLOBAL_VECTOR_STORE = store


def reset_vector_store() -> None:
    """Reset vector store singleton."""
    global _GLOBAL_VECTOR_STORE
    _GLOBAL_VECTOR_STORE = None


__all__ = [
    "VectorStoreRepository",
    "VectorStoreBoundaryRepository",
    "get_vector_store",
    "set_vector_store",
    "reset_vector_store",
]
