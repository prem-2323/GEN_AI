"""Phase 7 Grounding and Citation Validation Layer.

Deterministically verifies that student model outputs:
1. Only cite valid evidence IDs present in the supplied context.
2. Preserve exact numerical values without hallucinating numbers not found in source text.
3. Explicitly report grounding pass/fail status and list unsupported claims or invalid citations.
"""
from __future__ import annotations

import re
import logging
from typing import Any, Dict, List

log = logging.getLogger("gen-transform.rag.grounding_validator")

# Regex to find citation tags like [E1], [E2]
CITATION_TAG_RE = re.compile(r"\[E(\d+)\]")

# Regex to extract numeric values (percentages, floats, ints, e.g. 97.5%, 3050, 4)
NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?%?\b")


def validate_grounded_answer(
    answer: str,
    evidence_manifest: List[Dict[str, Any]],
    citations_map: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Validate student generated answer against supplied evidence manifest."""
    clean_answer = (answer or "").strip()

    # Handle insufficient evidence response
    if "insufficient to answer" in clean_answer.lower():
        return {
            "grounding_pass": True,
            "cited_evidence_ids": [],
            "unsupported_claims": [],
            "unsupported_numbers": [],
            "invalid_citations": [],
            "evidence_count": len(evidence_manifest),
            "citations_valid": True,
            "numerical_valid": True,
            "status_message": "Model correctly identified insufficient evidence.",
        }

    # 1. Extract citation IDs from answer
    raw_citation_matches = CITATION_TAG_RE.findall(clean_answer)
    cited_ids = sorted(list(set(f"E{m}" for m in raw_citation_matches)))

    # 2. Check for invalid citations
    invalid_citations = [cid for cid in cited_ids if cid not in citations_map]

    # 3. Concatenate all supplied evidence text for numerical cross-checking
    full_evidence_text = " ".join(item.get("text", "") for item in evidence_manifest)

    # 4. Check numerical values in answer against supplied evidence text
    answer_numbers = set(NUMBER_RE.findall(clean_answer))
    unsupported_numbers = []

    # Common non-data numbers to ignore (like list indexes 1., 2., etc.)
    for num in answer_numbers:
        # Normalize percentage comparison
        num_clean = num.rstrip("%")
        if num_clean not in full_evidence_text and num not in full_evidence_text:
            # Check if num is a small single digit that might be bullet point
            if num.isdigit() and int(num) <= 10:
                continue
            unsupported_numbers.append(num)

    unsupported_claims = []
    if invalid_citations:
        unsupported_claims.append(f"Answer cited unavailable evidence IDs: {invalid_citations}")
    if unsupported_numbers:
        unsupported_claims.append(f"Answer contains numerical values not found in evidence: {unsupported_numbers}")

    citations_valid = len(invalid_citations) == 0
    numerical_valid = len(unsupported_numbers) == 0
    grounding_pass = citations_valid and numerical_valid

    return {
        "grounding_pass": grounding_pass,
        "cited_evidence_ids": cited_ids,
        "unsupported_claims": unsupported_claims,
        "unsupported_numbers": sorted(unsupported_numbers),
        "invalid_citations": invalid_citations,
        "evidence_count": len(evidence_manifest),
        "citations_valid": citations_valid,
        "numerical_valid": numerical_valid,
        "status_message": "Grounding validation passed successfully." if grounding_pass else "Grounding issues detected.",
    }


__all__ = ["validate_grounded_answer"]
