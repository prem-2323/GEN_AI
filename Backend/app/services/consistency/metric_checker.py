"""Metric, number, percentage, and currency consistency checker (Phase 7)."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set
from ...models.validation import CheckItem

_NUM_RE = re.compile(r"\b(\d+(?:[.,]\d+)*)\b")
_PERCENT_RE = re.compile(r"\b(\d+(?:[.,]\d+)*)\s*(?:%|percent)\b", re.I)
_CURRENCY_RE = re.compile(r"(?:₹|Rs\.?|USD|\$|EUR|€)\s*(\d+(?:[.,]\d+)*(?:\s*(?:crore|lakh|million|billion|thousand|k|m|b))?)", re.I)


def _clean_num(raw: Any) -> Optional[float]:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    try:
        match = _NUM_RE.search(str(raw))
        if match:
            return float(match.group(1).replace(",", ""))
        return None
    except Exception:
        return None


def extract_numbers_from_text(text: str) -> List[float]:
    """Extracts raw numerical values from text."""
    nums = []
    for match in _NUM_RE.finditer(text):
        val = _clean_num(match.group(1))
        if val is not None:
            nums.append(val)
    return nums


def check_metric_consistency(uckr: Dict[str, Any], deliverable_text: str) -> List[CheckItem]:
    """Checks that all numbers and metrics from UCKR appear consistently without numerical contradiction."""
    checks: List[CheckItem] = []
    uckr_metrics = uckr.get("metrics", [])
    if not uckr_metrics:
        return checks

    deliv_nums = extract_numbers_from_text(deliverable_text)
    deliv_num_set: Set[float] = set(deliv_nums)

    # Split deliverable text into sentences for localized metric context checking
    sentences = [s.strip() for s in re.split(r"(?<=[.!?\n])\s+", deliverable_text) if s.strip()]

    for m in uckr_metrics:
        mid = m.get("metricId", "metric")
        raw_val = m.get("value")
        num_val = None
        if isinstance(raw_val, (int, float)):
            num_val = float(raw_val)
        elif isinstance(raw_val, str):
            num_val = _clean_num(raw_val)

        if num_val is None:
            continue

        unit = m.get("unit", "")
        ctx = m.get("context", "")
        name = m.get("name", "")

        # Check if preserved anywhere
        if num_val in deliv_num_set:
            checks.append(CheckItem(
                category="metric",
                factId=mid,
                expected=num_val,
                found=num_val,
                status="consistent",
                message=f"Metric '{num_val} {unit}' preserved consistently.",
                sourceSnippet=ctx[:100],
            ))

        # Check for sentence-level numerical contradiction
        anchors = set()
        if unit and len(unit.strip()) >= 3:
            anchors.add(unit.strip().lower())
        if name and not name.lower().startswith("metric_") and len(name.strip()) >= 3:
            anchors.add(name.strip().lower())

        # Extract words immediately adjacent to the number in context (e.g. "targeting 240 employees" -> "targeting", "employees")
        int_str = str(int(num_val) if num_val.is_integer() else num_val)
        for m_after in re.findall(rf"\b{int_str}\s+([a-zA-Z]{{3,}})", ctx):
            anchors.add(m_after.lower())
        for m_before in re.findall(rf"([a-zA-Z]{{3,}})\s+(?:\w+\s+)?{int_str}\b", ctx):
            anchors.add(m_before.lower())

        # Filter out generic stop words
        anchors = {a for a in anchors if a not in ("this", "that", "with", "from", "have", "been", "were", "metric", "count", "value")}

        if anchors and num_val not in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 2026):
            for s in sentences:
                s_lower = s.lower()
                if any(a in s_lower for a in anchors):
                    s_nums = extract_numbers_from_text(s)
                    if num_val not in s_nums:
                        for n in s_nums:
                            if n != num_val and n not in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 2026) and (0.1 * num_val <= n <= 10 * num_val):
                                checks.append(CheckItem(
                                    category="metric",
                                    factId=mid,
                                    expected=num_val,
                                    found=n,
                                    status="contradiction",
                                    message=f"Numerical mismatch: Expected {num_val} but found contradictory {n}.",
                                    sourceSnippet=s[:100],
                                ))
                                break

    return checks
