"""Phase 6 Embedding & Vector Search Pipeline Service.

Complete pipeline:
Extracted Text / Document -> Semantic Chunking -> Batch Embedding -> Vector Store -> Similarity Search.
"""
from __future__ import annotations

import time
import logging
from typing import Any, Dict, List, Optional, Tuple

from ..core.config import get_settings
from ..storage.repository import get_repository
from ..utils.helpers import utcnow_iso

from .chunker import SemanticChunker
from .config import EmbeddingConfig, default_embedding_config
from .embedder import EmbeddingModelInterface, get_embedder
from .metadata import build_chunk_metadata
from .models import (
    ChunkMetadata,
    IndexDocumentResponse,
    SearchRequest,
    SearchResult,
    SemanticChunk,
    VectorRecord,
)
from .repository import MemoryVectorStore, get_vector_store

log = logging.getLogger("gen-transform.embeddings.service")


class EmbeddingPipelineService:
    """Orchestrates complete Phase 6 Semantic Chunking, Embedding & Vector Search pipeline."""

    def __init__(
        self,
        config: Optional[EmbeddingConfig] = None,
        embedder: Optional[EmbeddingModelInterface] = None,
        vector_store: Optional[MemoryVectorStore] = None,
    ) -> None:
        self.config = config or default_embedding_config
        self.embedder = embedder
        self.store = vector_store
        self.chunker = SemanticChunker(self.config)

    def _get_embedder(self) -> EmbeddingModelInterface:
        if self.embedder is not None:
            return self.embedder
        return get_embedder()

    def _get_store(self) -> MemoryVectorStore:
        if self.store is not None:
            return self.store
        return get_vector_store()

    def index_text(
        self,
        text: str,
        document_id: str = "doc_001",
        source_filename: str = "",
        document_type: str = "document",
        page_texts: Optional[Dict[int, str]] = None,
    ) -> IndexDocumentResponse:
        """Run complete Phase 6 pipeline on raw document text."""
        t_start = time.time()
        log.info("Starting Phase 6 indexing for document '%s' (%d chars)", document_id, len(text))

        embedder = self._get_embedder()
        store = self._get_store()

        # Step 1: Semantic Chunking
        t_chunk_start = time.time()
        chunks: List[SemanticChunk] = self.chunker.chunk_text(
            text=text,
            document_id=document_id,
            page_texts=page_texts,
        )
        chunk_time_ms = round((time.time() - t_chunk_start) * 1000, 2)

        if not chunks:
            log.warning("No chunks generated for document '%s'", document_id)
            return IndexDocumentResponse(
                ok=True,
                document_id=document_id,
                status="empty",
                total_chunks=0,
                embedding_time_ms=0.0,
                index_time_ms=chunk_time_ms,
            )

        # Step 2: Idempotency & Clean previous vectors for re-indexing
        store.delete_document_vectors(document_id)

        # Step 3: Batch Embeddings Generation
        t_embed_start = time.time()
        chunk_texts = [c.text for c in chunks]

        # Process in batches
        all_vectors: List[List[float]] = []
        batch_size = max(1, self.config.batch_size)
        for i in range(0, len(chunk_texts), batch_size):
            batch_slice = chunk_texts[i : i + batch_size]
            batch_vecs = embedder.embed_batch(batch_slice)
            all_vectors.extend(batch_vecs)

        embedding_time_ms = round((time.time() - t_embed_start) * 1000, 2)

        # Step 4: Vector Store Ingestion
        t_index_start = time.time()
        records: List[VectorRecord] = []
        for chunk, vec in zip(chunks, all_vectors):
            meta = build_chunk_metadata(chunk, source_filename=source_filename, document_type=document_type)
            records.append(
                VectorRecord(
                    id=chunk.chunk_id,
                    vector=vec,
                    text=chunk.text,
                    metadata=meta,
                )
            )

        store.add_records(records)
        index_time_ms = round((time.time() - t_index_start) * 1000, 2)
        total_time_ms = round((time.time() - t_start) * 1000, 2)

        log.info(
            "Phase 6 indexing complete for '%s': %d chunks, embed_time=%sms, index_time=%sms, total=%sms",
            document_id,
            len(chunks),
            embedding_time_ms,
            index_time_ms,
            total_time_ms,
        )

        return IndexDocumentResponse(
            ok=True,
            document_id=document_id,
            status="indexed",
            total_chunks=len(chunks),
            embedding_time_ms=embedding_time_ms,
            index_time_ms=index_time_ms,
        )

    def index_document(self, document_id: str) -> IndexDocumentResponse:
        """Fetch extracted document from repository and run Phase 6 indexing pipeline."""
        sources_repo = get_repository("sources")
        doc = sources_repo.find_one({"id": document_id})

        text = ""
        doc_name = document_id
        page_texts: Dict[int, str] = {}

        if doc:
            doc_name = doc.get("name") or doc.get("filename", document_id)
            text = doc.get("extractedText", "")
            norm = doc.get("normalized", {}) if isinstance(doc, dict) else {}
            pages = norm.get("pages", []) or []
            if pages:
                for idx, p in enumerate(pages, start=1):
                    p_text = p.get("text", "")
                    if p_text:
                        page_texts[idx] = p_text

        if not text and not page_texts:
            log.warning("No text found in storage for document_id '%s'", document_id)

        return self.index_text(
            text=text,
            document_id=document_id,
            source_filename=doc_name,
            document_type="pdf" if doc_name.endswith(".pdf") else "document",
            page_texts=page_texts if page_texts else None,
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
        document_id: Optional[str] = None,
        section: Optional[str] = None,
        min_score: float = 0.0,
    ) -> Tuple[List[SearchResult], float]:
        """Perform semantic similarity search on query string; returns (results, search_latency_ms)."""
        t_start = time.time()
        clean_query = (query or "").strip()
        if not clean_query:
            return [], 0.0

        embedder = self._get_embedder()
        store = self._get_store()

        # Step 1: Embed query
        query_vector = embedder.embed_text(clean_query)

        # Step 2: Build filter dictionary
        filter_dict: Dict[str, Any] = {}
        if document_id:
            filter_dict["document_id"] = document_id
        if section:
            filter_dict["section"] = section

        # Step 3: Similarity search
        raw_results = store.similarity_search(
            query_vector=query_vector,
            top_k=top_k,
            filter_dict=filter_dict if filter_dict else None,
        )

        # Step 4: Min score filtering
        filtered = [r for r in raw_results if r.score >= min_score]
        latency_ms = round((time.time() - t_start) * 1000, 2)

        log.info("Semantic search for '%s' returned %d results (latency: %sms)", clean_query[:40], len(filtered), latency_ms)

        return filtered, latency_ms

    def delete_document_vectors(self, document_id: str) -> int:
        """Remove all vectors associated with document_id."""
        store = self._get_store()
        return store.delete_document_vectors(document_id)

    def reindex_document(self, document_id: str) -> IndexDocumentResponse:
        """Force re-index of a document (deletes old vectors and re-executes pipeline)."""
        self.delete_document_vectors(document_id)
        return self.index_document(document_id)

    def get_document_status(self, document_id: str) -> Dict[str, Any]:
        """Return indexing status and vector count for a document."""
        store = self._get_store()
        vecs = store.get_document_vectors(document_id)
        return {
            "ok": True,
            "document_id": document_id,
            "indexed": len(vecs) > 0,
            "total_vectors": len(vecs),
            "chunks": [v.metadata.model_dump() for v in vecs],
        }


_EMBEDDING_SERVICE_INSTANCE: Optional[EmbeddingPipelineService] = None


def get_embedding_service() -> EmbeddingPipelineService:
    """Return singleton instance of EmbeddingPipelineService."""
    global _EMBEDDING_SERVICE_INSTANCE
    if _EMBEDDING_SERVICE_INSTANCE is None:
        _EMBEDDING_SERVICE_INSTANCE = EmbeddingPipelineService()
    return _EMBEDDING_SERVICE_INSTANCE


def reset_embedding_service() -> None:
    """Reset singleton embedding service instance."""
    global _EMBEDDING_SERVICE_INSTANCE
    _EMBEDDING_SERVICE_INSTANCE = None


__all__ = ["EmbeddingPipelineService", "get_embedding_service", "reset_embedding_service"]
