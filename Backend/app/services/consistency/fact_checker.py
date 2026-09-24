"""Fact preservation and claim checker (Phase 7)."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Set
from ...models.validation import CheckItem

_WORD_RE = re.compile(r"\b[a-zA-Z0-9]{3,}\b")


def _get_words(text: str) -> Set[str]:
    return {w.lower() for w in _WORD_RE.findall(text or "")}


def check_fact_preservation(
    uckr: Dict[str, Any],
    deliverable_doc: Dict[str, Any],
    deliverable_text: str,
) -> List[CheckItem]:
    """Checks that facts referenced via usedFactIds are preserved with high fidelity."""
    checks: List[CheckItem] = []
    facts = uckr.get("facts", [])
    fact_map = {f.get("factId"): f for f in facts if f.get("factId")}

    used_fact_ids = deliverable_doc.get("usedFactIds", [])
    text_words = _get_words(deliverable_text)

    for fid in used_fact_ids:
        f_obj = fact_map.get(fid)
        if not f_obj:
            checks.append(CheckItem(
                category="fact",
                factId=fid,
                expected="Valid UCKR Fact",
                found=fid,
                status="contradiction",
                message=f"Unknown fact ID '{fid}' referenced in deliverable.",
            ))
            continue

        stmt = f_obj.get("statement", "")
        f_words = _get_words(stmt)
        if not f_words:
            continue

        overlap = len(f_words & text_words) / len(f_words)
        if overlap >= 0.35:
            checks.append(CheckItem(
                category="fact",
                factId=fid,
                expected=stmt[:80],
                found=f"Preserved ({int(overlap*100)}% match)",
                status="consistent",
                message=f"Fact '{fid}' accurately preserved.",
                sourceSnippet=stmt,
            ))
        else:
            checks.append(CheckItem(
                category="fact",
                factId=fid,
                expected=stmt[:80],
                found="Low presence in deliverable content",
                status="warning",
                message=f"Referenced fact '{fid}' has low presence in deliverable text.",
                sourceSnippet=stmt,
            ))

    return checks
