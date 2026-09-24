"""Fact processing, deduplication, and grounded source referencing."""
from __future__ import annotations

import re
import string
from typing import Any, Dict, List, Tuple
from ...models.uckr import Fact, SourceRef

_RISK_RE = re.compile(r"\b(risk|threat|vulnerab|attack|breach|critical|fail|loss|expos|malware|phishing|ransomware|cve)\b", re.I)
_ACTION_RE = re.compile(r"^(must|should|shall|need to|ensure|implement|deploy|update|patch|enforce|isolate|reset)\b", re.I)


def _normalize_text_for_dedup(text: str) -> str:
    """Lowercase and strip punctuation/extra whitespace for deduplication."""
    t = text.lower()
    t = t.translate(str.maketrans("", "", string.punctuation))
    return " ".join(t.split())


def classify_fact_type(statement: str, has_number: bool = False, has_date: bool = False) -> str:
    if _RISK_RE.search(statement):
        return "risk_fact"
    if has_number or re.search(r"\d", statement):
        return "metric_fact"
    if has_date or re.search(r"\b(January|February|March|April|May|June|July|August|September|October|November|December|\d{4})\b", statement, re.I):
        return "event_fact"
    if _ACTION_RE.search(statement.strip()):
        return "action_fact"
    return "proposition"


def process_and_deduplicate_facts(
    raw_facts: List[Any],
    source_id: str,
    page_texts: Dict[int, str],
    doc_name: str = "source",
) -> Tuple[List[Fact], List[str]]:
    """Deduplicates facts, attaches precise source references and page coordinates."""
    seen_hashes = set()
    facts: List[Fact] = []
    dropped_dupes: List[str] = []

    for i, item in enumerate(raw_facts):
        if isinstance(item, dict):
            stmt = (item.get("statement") or item.get("text") or item.get("value") or "").strip()
            quote = (item.get("quote") or (item.get("source") or {}).get("quote") if isinstance(item.get("source"), dict) else None) or stmt
            src_loc = item.get("source") if isinstance(item.get("source"), dict) else {}
            page_no = int(src_loc.get("page") or item.get("page") or 0)
            conf = float(item.get("confidence", 0.98))
            fact_type = item.get("type") or classify_fact_type(stmt)
        else:
            stmt = str(item).strip()
            quote = stmt
            page_no = 0
            conf = 0.95
            fact_type = classify_fact_type(stmt)

        if not stmt or len(stmt) < 5:
            continue

        norm_key = _normalize_text_for_dedup(stmt)
        if norm_key in seen_hashes:
            dropped_dupes.append(stmt)
            continue
        seen_hashes.add(norm_key)

        # Ground against source pages if page_no is not specified
        if page_no == 0:
            for pn, ptext in page_texts.items():
                if quote[:40] and quote[:40].lower() in ptext.lower():
                    page_no = pn
                    break
        page_no = page_no or 1

        fid = f"fact_{len(facts) + 1:03d}"
        chunk_id = f"chunk_{page_no:03d}"

        sref = SourceRef(
            sourceId=source_id,
            chunkId=chunk_id,
            pageNumber=page_no,
            textQuote=quote[:200],
        )

        fact = Fact(
            factId=fid,
            id=fid,
            statement=stmt,
            value=stmt,
            text=stmt,
            type=fact_type,
            confidence=round(conf, 3),
            sourceDoc=doc_name,
            page=page_no,
            chunkId=chunk_id,
            quote=quote,
            sourceRefs=[sref],
            usedInDeliverables=[],
        )
        facts.append(fact)

    return facts, dropped_dupes
