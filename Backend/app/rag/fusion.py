"""Phase 7 RAG — Hybrid Result Fusion & Deduplication Engine.

Combines heterogeneous vector search chunks and graph relationships using
configurable weighted scoring or Reciprocal Rank Fusion (RRF), performs deduplication,
detects vector-graph agreement, and checks for potential evidence contradictions.
"""
from __future__ import annotations

import time
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Set, Tuple

from .schemas import FusionStrategyEnum, RetrievalResult

log = logging.getLogger("gen-transform.rag.fusion")


class FusionStrategy(ABC):
    """Abstract Base Class for candidate fusion strategies."""

    @abstractmethod
    def fuse(
        self,
        vector_results: List[RetrievalResult],
        graph_results: List[RetrievalResult],
        vector_weight: float = 0.6,
        graph_weight: float = 0.4,
    ) -> List[RetrievalResult]:
        """Combine vector and graph results into unified scored candidate list."""
        pass


class WeightedScoreFusion(FusionStrategy):
    """Fuses vector and graph scores via normalized weighted linear combination."""

    def fuse(
        self,
        vector_results: List[RetrievalResult],
        graph_results: List[RetrievalResult],
        vector_weight: float = 0.6,
        graph_weight: float = 0.4,
    ) -> List[RetrievalResult]:
        total_weight = vector_weight + graph_weight
        w_v = vector_weight / total_weight if total_weight > 0 else 0.6
        w_g = graph_weight / total_weight if total_weight > 0 else 0.4

        fused: List[RetrievalResult] = []

        for item in vector_results:
            item_copy = item.model_copy()
            item_copy.score = float(item.score * w_v)
            fused.append(item_copy)

        for item in graph_results:
            item_copy = item.model_copy()
            item_copy.score = float(item.score * w_g)
            fused.append(item_copy)

        fused.sort(key=lambda x: x.score, reverse=True)
        return fused


class ReciprocalRankFusion(FusionStrategy):
    """Fuses heterogeneous retrieval results using Reciprocal Rank Fusion (RRF)."""

    def __init__(self, k: int = 60) -> None:
        self.k = k

    def fuse(
        self,
        vector_results: List[RetrievalResult],
        graph_results: List[RetrievalResult],
        vector_weight: float = 0.6,
        graph_weight: float = 0.4,
    ) -> List[RetrievalResult]:
        scores: Dict[str, float] = {}
        item_map: Dict[str, RetrievalResult] = {}

        # Process vector ranks
        for rank, item in enumerate(vector_results, start=1):
            key = f"vector_{item.source_id}"
            rrf_contrib = 1.0 / (self.k + rank)
            scores[key] = scores.get(key, 0.0) + rrf_contrib * vector_weight
            item_map[key] = item

        # Process graph ranks
        for rank, item in enumerate(graph_results, start=1):
            key = f"graph_{item.source_id}"
            rrf_contrib = 1.0 / (self.k + rank)
            scores[key] = scores.get(key, 0.0) + rrf_contrib * graph_weight
            item_map[key] = item

        fused: List[RetrievalResult] = []
        for key, rrf_score in scores.items():
            original_item = item_map[key]
            item_copy = original_item.model_copy()
            item_copy.score = float(rrf_score)
            fused.append(item_copy)

        fused.sort(key=lambda x: x.score, reverse=True)
        return fused


class ResultFusion:
    """Orchestrates fusion, deduplication, agreement detection, and contradiction auditing."""

    def __init__(self, default_strategy: FusionStrategyEnum = FusionStrategyEnum.WEIGHTED) -> None:
        self.weighted_fusion = WeightedScoreFusion()
        self.rrf_fusion = ReciprocalRankFusion(k=60)
        self.default_strategy = default_strategy

    def fuse_and_deduplicate(
        self,
        vector_results: List[RetrievalResult],
        graph_results: List[RetrievalResult],
        strategy: FusionStrategyEnum = FusionStrategyEnum.WEIGHTED,
        vector_weight: float = 0.6,
        graph_weight: float = 0.4,
    ) -> Tuple[List[RetrievalResult], bool, List[Dict[str, Any]], float]:
        """Perform result fusion, remove exact duplicate evidence, audit agreement and contradictions."""
        t_start = time.time()

        # Step 1: Select Fusion Strategy
        fusion_engine: FusionStrategy = (
            self.rrf_fusion if strategy == FusionStrategyEnum.RRF else self.weighted_fusion
        )

        fused_items = fusion_engine.fuse(
            vector_results=vector_results,
            graph_results=graph_results,
            vector_weight=vector_weight,
            graph_weight=graph_weight,
        )

        # Step 2: Deduplication
        deduped: List[RetrievalResult] = []
        seen_keys: Set[str] = set()

        for item in fused_items:
            # Key based on source_type + source_id or content signature
            clean_text_sig = "".join(item.text.lower().split())[:80]
            dedup_key = f"{item.source_type}_{item.source_id}"
            text_key = f"sig_{clean_text_sig}"

            if dedup_key in seen_keys or text_key in seen_keys:
                continue

            seen_keys.add(dedup_key)
            seen_keys.add(text_key)
            deduped.append(item)

        # Step 3: Graph + Vector Agreement Detection
        agreement_detected = False
        vector_texts = [r.text.lower() for r in vector_results]
        graph_triples: List[Tuple[str, str, str]] = []

        for gr in graph_results:
            src = str(gr.metadata.get("source", "")).lower()
            rel = str(gr.metadata.get("relation", "")).lower()
            tgt = str(gr.metadata.get("target", "")).lower()
            if src and tgt:
                graph_triples.append((src, rel, tgt))

        for v_text in vector_texts:
            for src, rel, tgt in graph_triples:
                if src in v_text and tgt in v_text:
                    agreement_detected = True
                    break
            if agreement_detected:
                break

        # Step 4: Contradiction / Conflict Detection
        potential_conflicts: List[Dict[str, Any]] = []
        for gr in graph_results:
            src = str(gr.metadata.get("source", "")).lower()
            rel = str(gr.metadata.get("relation", "")).lower()
            tgt = str(gr.metadata.get("target", "")).lower()
            if not src or not tgt:
                continue

            for vr in vector_results:
                v_text_lower = vr.text.lower()
                # Simple negation or conflict heuristic
                if src in v_text_lower and tgt in v_text_lower:
                    negation_cues = ["not", "no longer", "never", "replaced", "deprecated", "does not use"]
                    if any(cue in v_text_lower for cue in negation_cues):
                        potential_conflicts.append({
                            "type": "vector_graph_discrepancy",
                            "graph_relationship": f"{gr.metadata.get('source')} --[{gr.metadata.get('relation')}]--> {gr.metadata.get('target')}",
                            "vector_chunk_id": vr.source_id,
                            "vector_snippet": vr.text[:120],
                            "reason": "Vector chunk contains negation or replacement terms regarding graph relationship."
                        })

        latency_ms = round((time.time() - t_start) * 1000, 2)
        log.debug(
            "Result fusion complete: fused=%d -> deduped=%d, agreement=%s, conflicts=%d, latency=%sms",
            len(fused_items),
            len(deduped),
            agreement_detected,
            len(potential_conflicts),
            latency_ms,
        )

        return deduped, agreement_detected, potential_conflicts, latency_ms


__all__ = ["ResultFusion", "FusionStrategy", "WeightedScoreFusion", "ReciprocalRankFusion"]
