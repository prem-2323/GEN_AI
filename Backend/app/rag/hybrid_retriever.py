"""Phase 5 — Hybrid Vector + Graph Retriever.

Combines REAL Vector Retrieval (FAISS + BGE embeddings) with
REAL Graph Retrieval (Neo4j parameterized Cypher) using
Reciprocal Rank Fusion (RRF) and identifier deduplication.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from ..core.config import get_settings
from .fusion import ReciprocalRankFusion, ResultFusion
from .graph_retriever import GraphRetriever
from .query_analyzer import QueryAnalyzer
from .schemas import FusionStrategyEnum, RetrievalResult
from .vector_retriever import VectorRetriever

log = logging.getLogger("gen-transform.rag.hybrid_retriever")


class HybridRetriever:
    """Orchestrates dual vector + graph retrieval with transparent RRF fusion."""

    def __init__(
        self,
        vector_retriever: Optional[VectorRetriever] = None,
        graph_retriever: Optional[GraphRetriever] = None,
        query_analyzer: Optional[QueryAnalyzer] = None,
        rrf_k: Optional[int] = None,
    ) -> None:
        self.settings = get_settings()
        self.vector_retriever = vector_retriever or VectorRetriever()
        self.graph_retriever = graph_retriever or GraphRetriever()
        self.query_analyzer = query_analyzer or QueryAnalyzer()
        self.rrf_k = rrf_k if rrf_k is not None else getattr(self.settings, "rrf_k", 60)
        self.vector_top_k = getattr(self.settings, "vector_top_k", 10)
        self.graph_top_k = getattr(self.settings, "graph_top_k", 10)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        document_id: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Execute full hybrid retrieval pipeline.
        
        query
         ↓
        VectorRetriever (FAISS + BGE)
         ↓
        GraphRetriever (Neo4j)
         ↓
        Normalize
         ↓
        Deduplicate
         ↓
        RRF
         ↓
        Final top-k evidence
        """
        t_total_start = time.time()

        # Step 1: Query Analysis
        analysis = self.query_analyzer.analyze(query)

        # Step 2: Vector Retrieval (BGE embeddings + FAISS)
        t_vec_start = time.time()
        vector_results, embedding_time_ms = self.vector_retriever.retrieve(
            query=analysis.semantic_query,
            top_k=self.vector_top_k,
            document_id=document_id,
        )
        faiss_search_time_ms = round((time.time() - t_vec_start) * 1000, 2)

        # Step 3: Graph Retrieval (Neo4j Parameterized Cypher)
        t_graph_start = time.time()
        graph_results: List[RetrievalResult] = []
        try:
            graph_results, _ = self.graph_retriever.retrieve(
                analysis=analysis,
                graph_depth=1,
                document_id=document_id,
                top_k=self.graph_top_k,
            )
        except ConnectionError as ce:
            log.warning("Neo4j database offline during hybrid retrieval: %s", ce)
        except Exception as exc:
            log.warning("Graph retrieval encountered error: %s", exc)
        neo4j_search_time_ms = round((time.time() - t_graph_start) * 1000, 2)

        # Step 4: Normalize Vector & Graph Candidates
        normalized_vector = self._normalize_candidates(vector_results, method="vector")
        normalized_graph = self._normalize_candidates(graph_results, method="graph")

        # Step 5: Reciprocal Rank Fusion & Deduplication
        t_fusion_start = time.time()
        fused_items = self._rrf_fuse_and_deduplicate(
            vector_items=normalized_vector,
            graph_items=normalized_graph,
            k=self.rrf_k,
        )
        fusion_time_ms = round((time.time() - t_fusion_start) * 1000, 2)

        # Step 6: Select Top-K
        final_top_k = fused_items[:top_k]
        for rank_idx, item in enumerate(final_top_k, start=1):
            item["final_rank"] = rank_idx
            item["rank"] = rank_idx

        total_time_ms = round((time.time() - t_total_start) * 1000, 2)

        metrics = {
            "embedding_time": embedding_time_ms,
            "faiss_search_time": faiss_search_time_ms,
            "neo4j_search_time": neo4j_search_time_ms,
            "fusion_time": fusion_time_ms,
            "total_time": total_time_ms,
            "vector_candidates": len(vector_results),
            "graph_candidates": len(graph_results),
            "fused_count": len(fused_items),
            "top_k": len(final_top_k),
            "rrf_k": self.rrf_k,
        }

        return final_top_k, metrics

    def _normalize_candidates(
        self,
        results: List[RetrievalResult],
        method: str,
    ) -> List[Dict[str, Any]]:
        """Normalize retrieval candidates into common schema with 1-based ranks."""
        normalized = []
        for rank, r in enumerate(results, start=1):
            meta = r.metadata or {}
            ev = r.evidence or {}
            page = meta.get("page_start") or meta.get("page") or ev.get("page", 1)
            chunk_id = r.source_id or ev.get("chunk_id", "")
            doc_id = r.document_id or meta.get("document_id", "") or ev.get("document_id", "")

            normalized.append({
                "id": chunk_id or f"{method}_{rank}",
                "document_id": doc_id,
                "chunk_id": chunk_id,
                "text": r.text,
                "page_number": int(page) if page else 1,
                "source": r.source_type or method,
                "retrieval_method": method,
                "rank": rank,
                "score": float(r.score),
                "metadata": meta,
            })
        return normalized

    def _rrf_fuse_and_deduplicate(
        self,
        vector_items: List[Dict[str, Any]],
        graph_items: List[Dict[str, Any]],
        k: int = 60,
    ) -> List[Dict[str, Any]]:
        """Calculate transparent RRF score and deduplicate by stable identifiers."""
        # Maps for quick lookup: identifier -> RRF accumulator
        # Stable identifier keys: chunk_id, text signature, or source_id
        entry_map: Dict[str, Dict[str, Any]] = {}
        rrf_scores: Dict[str, float] = {}
        vector_ranks: Dict[str, int] = {}
        graph_ranks: Dict[str, int] = {}

        # 1. Process vector candidates
        for item in vector_items:
            stable_id = item.get("chunk_id") or item.get("id") or item["text"][:64]
            text_sig = "".join(item["text"].lower().split())[:80]
            canonical_key = stable_id if stable_id else text_sig

            v_rank = item["rank"]
            vector_ranks[canonical_key] = v_rank
            contrib = 1.0 / (k + v_rank)
            rrf_scores[canonical_key] = rrf_scores.get(canonical_key, 0.0) + contrib
            if canonical_key not in entry_map:
                entry_map[canonical_key] = item

        # 2. Process graph candidates
        for item in graph_items:
            stable_id = item.get("chunk_id") or item.get("id") or item["text"][:64]
            text_sig = "".join(item["text"].lower().split())[:80]
            canonical_key = stable_id if stable_id in entry_map else text_sig

            g_rank = item["rank"]
            graph_ranks[canonical_key] = g_rank
            contrib = 1.0 / (k + g_rank)
            rrf_scores[canonical_key] = rrf_scores.get(canonical_key, 0.0) + contrib
            if canonical_key not in entry_map:
                entry_map[canonical_key] = item

        # 3. Assemble fused list
        fused = []
        for key, base_item in entry_map.items():
            final_score = rrf_scores[key]
            item_copy = dict(base_item)
            item_copy["rrf_score"] = round(final_score, 6)
            item_copy["score"] = round(final_score, 6)
            item_copy["vector_rank"] = vector_ranks.get(key)
            item_copy["graph_rank"] = graph_ranks.get(key)
            item_copy["retrieval_method"] = (
                "hybrid" if (key in vector_ranks and key in graph_ranks)
                else base_item["retrieval_method"]
            )
            fused.append(item_copy)

        # Sort by RRF score descending
        fused.sort(key=lambda x: x["rrf_score"], reverse=True)
        return fused


__all__ = ["HybridRetriever"]
