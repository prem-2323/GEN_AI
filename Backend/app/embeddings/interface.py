"""Vector Store & Embeddings Boundary Interface (Phase 2 Preparation).

Semantic chunking and embedding generation belong to Phase 6.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class VectorStoreInterface(ABC):
    """Abstract interface for Vector Store operations."""

    @abstractmethod
    def add_vectors(self, ids: List[str], vectors: List[List[float]], metadata: List[Dict[str, Any]]) -> bool:
        pass

    @abstractmethod
    def similarity_search(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        pass
