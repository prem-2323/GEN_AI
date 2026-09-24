"""Unsupported Claim and Hallucination Detector (Phase 7)."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Set

_CURRENCY_CLAIM_RE = re.compile(r"(?:₹|Rs\.?|USD|\$|EUR|€)\s*\d+(?:[.,]\d+)*(?:\s*(?:crore|lakh|million|billion|thousand|k|m|b))?", re.I)
_NUM_RE = re.compile(r"\b\d{2,}(?:[.,]\d+)*\b")


def _flatten_uckr_text(uckr: Dict[str, Any]) -> str:
    parts: List[str] = [uckr.get("title", ""), uckr.get("summary", "")]
    for f in uckr.get("facts", []):
        parts.append(f.get("statement", ""))
    for m in uckr.get("metrics", []):
        parts.append(f"{m.get('value')} {m.get('unit')} {m.get('context')}")
    for c in uckr.get("claims", []):
        parts.append(c.get("statement", ""))
    for a in uckr.get("actions", []):
        parts.append(a.get("action", ""))
    return " ".join(parts).lower()


def detect_unsupported_claims(uckr: Dict[str, Any], deliverable_text: str) -> List[str]:
    """Identifies monetary claims, ungrounded metrics, and numbers in deliverable not in UCKR."""
    unsupported: List[str] = []
    uckr_flat = _flatten_uckr_text(uckr)

    # 1. Detect currency amounts in deliverable
    deliv_currencies = _CURRENCY_CLAIM_RE.findall(deliverable_text)
    uckr_currencies = _CURRENCY_CLAIM_RE.findall(uckr_flat)
    uckr_curr_set: Set[str] = {c.lower().replace(" ", "") for c in uckr_currencies}

    for c_claim in deliv_currencies:
        normalized = c_claim.lower().replace(" ", "")
        if normalized not in uckr_curr_set:
            unsupported.append(f"Financial figure '{c_claim}' has no supporting evidence in UCKR.")

    # 2. Detect ungrounded large numbers (excluding common years like 2026, slide indices 1-10)
    deliv_nums = set(_NUM_RE.findall(deliverable_text))
    uckr_nums = set(_NUM_RE.findall(uckr_flat))

    for num in deliv_nums:
        # Ignore dates like 2026 or small section counts
        if num in ("2024", "2025", "2026", "2027") or len(num) <= 2:
            continue
        if num not in uckr_nums:
            unsupported.append(f"Ungrounded numerical value '{num}' not found in source knowledge representation.")

    return unsupported
