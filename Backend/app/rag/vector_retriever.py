"""Phase 7 RAG — Vector Search Retriever.

Interfaces with Phase 6 Embedding Pipeline Service to perform semantic vector search
and standardize outputs into standard RetrievalResult format.
"""
from __future__ import annotations

import time
import logging
from typing import List, Optional, Tuple

from ..embeddings.service import EmbeddingPipelineService, get_embedding_service
from .schemas import RetrievalResult

log = logging.getLogger("gen-transform.rag.vector_retriever")


class VectorRetriever:
    """Retrieves semantically relevant document chunks using vector embeddings."""

    def __init__(self, service: Optional[EmbeddingPipelineService] = None) -> None:
        self.service = service

    def _get_service(self) -> EmbeddingPipelineService:
        if self.service is not None:
            return self.service
        return get_embedding_service()

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        document_id: Optional[str] = None,
        min_score: float = 0.0,
    ) -> Tuple[List[RetrievalResult], float]:
        """Perform semantic similarity search and map to standard RetrievalResult."""
        t_start = time.time()
        service = self._get_service()

        raw_results, search_latency = service.search(
            query=query,
            top_k=top_k,
            document_id=document_id,
            min_score=min_score,
        )

        results: List[RetrievalResult] = []
        for res in raw_results:
            meta = res.metadata.model_dump() if hasattr(res.metadata, "model_dump") else dict(res.metadata)
            doc_id = res.document_id or meta.get("document_id", "")
            page = meta.get("page_number") or meta.get("page", 1)

            results.append(
                RetrievalResult(
                    source_type="vector",
                    source_id=res.chunk_id,
                    document_id=doc_id,
                    text=res.text,
                    score=float(res.score),
                    metadata=meta,
                    evidence={
                        "chunk_id": res.chunk_id,
                        "page": page,
                        "document_id": doc_id,
                        "filename": meta.get("source_filename", ""),
                        "section": meta.get("section", ""),
                    },
                )
            )

        latency_ms = round((time.time() - t_start) * 1000, 2)
        log.debug("Vector retriever found %d items in %sms", len(results), latency_ms)
        return results, latency_ms


__all__ = ["VectorRetriever"]
