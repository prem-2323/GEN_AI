"""Phase 7 RAG — Context & Evidence Validator.

Audits retrieved evidence quality and coverage against configurable threshold rules
to ensure factual grounding and handle 'Insufficient Evidence' cases gracefully.
"""
from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from .schemas import RetrievalResult

log = logging.getLogger("gen-transform.rag.validator")


class ContextValidator:
    """Evaluates context sufficiency before prompt generation."""

    def __init__(self, default_min_score: float = 0.0) -> None:
        self.default_min_score = default_min_score

    def validate(
        self,
        candidates: List[RetrievalResult],
        min_retrieval_score: float = 0.0,
    ) -> Tuple[bool, Optional[str]]:
        """Check if retrieved evidence meets minimum coverage and score thresholds."""
        threshold = max(self.default_min_score, min_retrieval_score)

        if not candidates:
            log.warning("Context validation failed: No retrieval candidates present.")
            return False, "No relevant vector chunks or graph relationships were found for this query."

        max_score = max(c.score for c in candidates)
        if threshold > 0.0 and max_score < threshold:
            log.warning(
                "Context validation failed: max retrieval score (%.3f) is below threshold (%.3f).",
                max_score,
                threshold,
            )
            return False, f"Retrieved evidence score ({max_score:.2f}) is below the required confidence threshold ({threshold:.2f})."

        log.debug("Context validation passed with %d candidates (max score: %.3f)", len(candidates), max_score)
        return True, None


__all__ = ["ContextValidator"]
