"""Phase 4 — Vector Store Repository & Factory.

Production factory that selects FAISS or MemoryVectorStore based on VECTOR_BACKEND config.
NO silent fallback: if VECTOR_BACKEND=faiss and FAISS is unavailable, raise a clear error.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union

from .interface import VectorStoreInterface
from .models import SearchResult, VectorRecord

log = logging.getLogger("gen-transform.embeddings.repository")


class VectorStoreRepository(VectorStoreInterface):
    """Production Repository adapter delegating to underlying Vector Store implementation."""

    def __init__(self, store: Optional[VectorStoreInterface] = None) -> None:
        self.store = store or _create_vector_store()

    def add_vectors(
        self,
        ids: List[str],
        vectors: List[List[float]],
        metadata: List[Dict[str, Any]],
    ) -> bool:
        return self.store.add_vectors(ids, vectors, metadata)

    def add_records(self, records: List[VectorRecord]) -> bool:
        if hasattr(self.store, "add_records"):
            return self.store.add_records(records)
        # Fallback to add_vectors for interface compatibility
        ids = [r.id for r in records]
        vectors = [r.vector for r in records]
        metadata = []
        for r in records:
            m = r.metadata.model_dump()
            m["text"] = r.text
            metadata.append(m)
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


def _create_vector_store() -> VectorStoreInterface:
    """Factory that creates the correct vector store backend based on VECTOR_BACKEND config.

    VECTOR_BACKEND=faiss  → FAISSVectorStore (production, persistent)
    VECTOR_BACKEND=memory → MemoryVectorStore (testing only)

    Rules:
    - If VECTOR_BACKEND=faiss and FAISS import fails → raise RuntimeError (NO silent fallback)
    - If VECTOR_BACKEND is unrecognized → raise ValueError
    """
    from ..core.config import get_settings

    settings = get_settings()
    backend = getattr(settings, "vector_backend", "faiss").lower().strip()

    if backend == "faiss":
        try:
            from .faiss_store import FAISSVectorStore

            dimension = getattr(settings, "vector_dimension", 384)
            store = FAISSVectorStore(dimension=dimension)
            log.info(
                "Initialized FAISSVectorStore (dim=%d, dir='%s')",
                dimension,
                store.persistence_dir,
            )
            return store
        except ImportError as exc:
            raise RuntimeError(
                "VECTOR_BACKEND=faiss but FAISS is not installed. "
                "Install with: pip install faiss-cpu\n"
                "Or set VECTOR_BACKEND=memory for testing."
            ) from exc
        except Exception as exc:
            raise RuntimeError(
                f"VECTOR_BACKEND=faiss but FAISSVectorStore initialization failed: {exc}\n"
                "Check FAISS installation and STORAGE_ROOT permissions."
            ) from exc

    elif backend in ("memory", "mock"):
        from .vector_store import MemoryVectorStore

        log.warning(
            "Using MemoryVectorStore (VECTOR_BACKEND=%s). "
            "This is NOT suitable for production use.",
            backend,
        )
        return MemoryVectorStore()

    else:
        raise ValueError(
            f"Unknown VECTOR_BACKEND='{backend}'. "
            "Supported values: 'faiss' (production), 'memory' (testing)."
        )


_GLOBAL_VECTOR_STORE: Optional[VectorStoreInterface] = None


def get_vector_store() -> VectorStoreInterface:
    """Get singleton VectorStore instance (FAISS or Memory based on config)."""
    global _GLOBAL_VECTOR_STORE
    if _GLOBAL_VECTOR_STORE is None:
        _GLOBAL_VECTOR_STORE = _create_vector_store()
    return _GLOBAL_VECTOR_STORE


def set_vector_store(store: VectorStoreInterface) -> None:
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
