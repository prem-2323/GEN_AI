"""Date consistency checker with ISO normalization (Phase 7)."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from ...models.validation import CheckItem

_MONTH_MAP = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

_DATE_PATTERNS = [
    # YYYY-MM-DD
    re.compile(r"\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b"),
    # DD Month YYYY (e.g. 15 August 2026)
    re.compile(r"\b(\d{1,2})\s+([A-Za-z]+),?\s+(\d{4})\b", re.I),
    # Month DD, YYYY (e.g. August 15, 2026)
    re.compile(r"\b([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})\b", re.I),
    # DD/MM/YYYY
    re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b"),
]


def normalize_date_to_iso(text: str) -> Optional[str]:
    """Parses a date string into ISO standard YYYY-MM-DD format."""
    if not text or not isinstance(text, str):
        return None
    raw = text.strip()

    # Direct match if already YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", raw):
        return raw

    # 1. YYYY-MM-DD
    m1 = re.search(r"\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b", raw)
    if m1:
        y, m, d = int(m1.group(1)), int(m1.group(2)), int(m1.group(3))
        if 1 <= m <= 12 and 1 <= d <= 31:
            return f"{y:04d}-{m:02d}-{d:02d}"

    # 2. DD Month YYYY (e.g. 15 August 2026)
    m2 = re.search(r"\b(\d{1,2})\s+([A-Za-z]+),?\s+(\d{4})\b", raw)
    if m2:
        d, mon_str, y = int(m2.group(1)), m2.group(2).lower(), int(m2.group(3))
        m_num = _MONTH_MAP.get(mon_str)
        if m_num and 1 <= d <= 31:
            return f"{y:04d}-{m_num:02d}-{d:02d}"

    # 3. Month DD, YYYY (e.g. August 15, 2026)
    m3 = re.search(r"\b([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})\b", raw)
    if m3:
        mon_str, d, y = m3.group(1).lower(), int(m3.group(2)), int(m3.group(3))
        m_num = _MONTH_MAP.get(mon_str)
        if m_num and 1 <= d <= 31:
            return f"{y:04d}-{m_num:02d}-{d:02d}"

    # 4. DD/MM/YYYY
    m4 = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", raw)
    if m4:
        d, m, y = int(m4.group(1)), int(m4.group(2)), int(m4.group(3))
        if 1 <= m <= 12 and 1 <= d <= 31:
            return f"{y:04d}-{m:02d}-{d:02d}"

    return None


def extract_all_dates_from_text(text: str) -> List[Tuple[str, str]]:
    """Extracts all recognized dates as tuples: (raw_string, iso_string)."""
    found: List[Tuple[str, str]] = []
    if not text:
        return found

    for pat in _DATE_PATTERNS:
        for match in pat.finditer(text):
            raw_match = match.group(0)
            iso = normalize_date_to_iso(raw_match)
            if iso:
                found.append((raw_match, iso))
    return found


def check_date_consistency(uckr: Dict[str, Any], deliverable_text: str) -> List[CheckItem]:
    """Checks date statements between UCKR events/facts and deliverable text."""
    checks: List[CheckItem] = []
    uckr_dates: List[Tuple[str, str, str]] = []  # (source_id, raw_date, iso_date)

    # 1. Collect dates from UCKR events
    for ev in uckr.get("events", []):
        d_str = ev.get("date")
        if d_str:
            iso = normalize_date_to_iso(d_str)
            if iso:
                uckr_dates.append((ev.get("eventId", "event"), d_str, iso))

    # 2. Collect dates from UCKR facts/metrics
    for f in uckr.get("facts", []):
        stmt = f.get("statement", "")
        f_dates = extract_all_dates_from_text(stmt)
        for raw_d, iso_d in f_dates:
            uckr_dates.append((f.get("factId", "fact"), raw_d, iso_d))

    if not uckr_dates:
        return checks

    # Extract all dates from the deliverable text
    deliv_dates = extract_all_dates_from_text(deliverable_text)
    deliv_iso_set = {iso for _, iso in deliv_dates}

    for src_id, u_raw, u_iso in uckr_dates:
        if u_iso in deliv_iso_set:
            checks.append(CheckItem(
                category="date",
                factId=src_id if "fact" in src_id else None,
                expected=u_iso,
                found=u_iso,
                status="consistent",
                message=f"Date '{u_raw}' correctly preserved as {u_iso}.",
            ))
        else:
            # Check for close conflicting dates (e.g. same year and month with altered day)
            conflicts = [iso for iso in deliv_iso_set if iso != u_iso and len(iso) >= 7 and len(u_iso) >= 7 and iso[:7] == u_iso[:7]]
            if conflicts:
                checks.append(CheckItem(
                    category="date",
                    factId=src_id if "fact" in src_id else None,
                    expected=u_iso,
                    found=conflicts[0],
                    status="contradiction",
                    message=f"Date contradiction: Expected {u_iso} ({u_raw}) but found {conflicts[0]}.",
                ))

    return checks
