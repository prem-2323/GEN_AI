"""Phase 7 RAG — Reranking Subsystem.

Provides RerankerInterface abstraction and a LightweightReranker implementation that orders
retrieval candidates based on query relevance, term overlap, and exact entity matches.
"""
from __future__ import annotations

import re
import time
import logging
from abc import ABC, abstractmethod
from typing import List, Tuple

from .schemas import RetrievalResult

log = logging.getLogger("gen-transform.rag.reranker")


class RerankerInterface(ABC):
    """Abstract Base Class for evidence reranking implementations."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: List[RetrievalResult],
        top_n: int = 5,
    ) -> Tuple[List[RetrievalResult], float]:
        """Rerank candidates based on query relevance and select top_n items."""
        pass


class LightweightReranker(RerankerInterface):
    """Fast, deterministic reranker scoring candidates using term density and entity alignment."""

    def rerank(
        self,
        query: str,
        candidates: List[RetrievalResult],
        top_n: int = 5,
    ) -> Tuple[List[RetrievalResult], float]:
        t_start = time.time()
        clean_query = (query or "").lower().strip()
        if not candidates or not clean_query:
            return candidates[:top_n], 0.0

        query_tokens = set(re.findall(r"\b[a-zA-Z0-9\-_]{2,}\b", clean_query))

        scored_candidates: List[Tuple[float, RetrievalResult]] = []
        for cand in candidates:
            text_lower = cand.text.lower()
            text_tokens = set(re.findall(r"\b[a-zA-Z0-9\-_]{2,}\b", text_lower))

            # 1. Base Retrieval Score
            score = cand.score * 0.4

            # 2. Token Jaccard / Overlap Ratio
            if query_tokens and text_tokens:
                overlap = len(query_tokens.intersection(text_tokens))
                token_score = overlap / len(query_tokens)
                score += token_score * 0.35

            # 3. Exact Query Phrase Match Bonus
            if clean_query in text_lower:
                score += 0.15

            # 4. Entity Match Bonus
            if cand.source_type == "graph":
                src = str(cand.metadata.get("source", "")).lower()
                tgt = str(cand.metadata.get("target", "")).lower()
                if (src and src in clean_query) or (tgt and tgt in clean_query):
                    score += 0.10

            cand_copy = cand.model_copy()
            cand_copy.score = round(score, 4)
            scored_candidates.append((score, cand_copy))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        reranked = [item[1] for item in scored_candidates[:top_n]]

        latency_ms = round((time.time() - t_start) * 1000, 2)
        log.debug("Lightweight reranker completed: in=%d -> out=%d in %sms", len(candidates), len(reranked), latency_ms)
        return reranked, latency_ms


__all__ = ["RerankerInterface", "LightweightReranker"]
