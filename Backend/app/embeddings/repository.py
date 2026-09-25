"""Placeholder Vector Store Repository (Phase 2 Architectural Boundary).

Does not execute embedding generation or vector searches in Phase 2.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from .interface import VectorStoreInterface

log = logging.getLogger("gen-transform.embeddings")


class VectorStoreBoundaryRepository(VectorStoreInterface):
    """Architectural boundary placeholder for Vector Storage (Phase 6)."""

    def add_vectors(self, ids: List[str], vectors: List[List[float]], metadata: List[Dict[str, Any]]) -> bool:
        log.debug("VectorStore boundary: add_vectors deferred to Phase 6 (count=%d)", len(ids))
        return True

    def similarity_search(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        log.debug("VectorStore boundary: similarity_search deferred to Phase 6")
        return []
