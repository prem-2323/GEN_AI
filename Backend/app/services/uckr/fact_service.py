"""Fact processing, deduplication, sentence-level boundary repair, and grounded source referencing."""
from __future__ import annotations

import re
import string
from typing import Any, Dict, List, Optional, Set, Tuple
from ...models.uckr import Fact, SourceRef

_RISK_RE = re.compile(r"\b(risk|threat|vulnerab|attack|breach|critical|fail|loss|expos|malware|phishing|ransomware|cve|depend|over-relian)\b", re.I)
_ACTION_RE = re.compile(r"^(must|should|shall|need to|needs to|ensure|implement|deploy|update|patch|enforce|isolate|reset|preserve|maintain|remain)\b", re.I)
_FRAGMENT_START_RE = re.compile(r"^(and\s+|or\s+|as\s+well\s+as\s+|which\s+|where\s+|that\s+)", re.I)


def _normalize_text_for_dedup(text: str) -> str:
    """Lowercase and strip punctuation/extra whitespace for deduplication."""
    t = text.lower()
    t = t.translate(str.maketrans("", "", string.punctuation))
    return " ".join(t.split())


def split_into_sentences(text: str) -> List[str]:
    """Clean sentence boundary detection that preserves coordinated clauses (never splits on 'and', 'or', commas)."""
    if not text:
        return []
    # Normalize carriage returns
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    # Split on paragraph breaks or terminal punctuation (. ! ?) followed by whitespace
    raw_splits = re.split(r"(?<=[.!?])\s+|\n{2,}", normalized)
    sentences = []
    for s in raw_splits:
        cleaned = s.strip()
        if len(cleaned) > 5:
            # Strip bullet prefixes
            cleaned = re.sub(r"^[\s•\-\*\d\.\)\:]+", "", cleaned).strip()
            if cleaned:
                sentences.append(cleaned)
    return sentences


def validate_fact(fact_text: str, source_text: str) -> bool:
    """Check that an extracted fact is actually grounded and supported in the source text."""
    if not fact_text or not source_text:
        return False
    norm_fact = _normalize_text_for_dedup(fact_text)
    norm_source = _normalize_text_for_dedup(source_text)
    if not norm_fact:
        return False
    if norm_fact in norm_source:
        return True

    # Token overlap check (>= 75% of content words must exist in source)
    fact_words = [w for w in norm_fact.split() if len(w) > 3]
    if not fact_words:
        return True
    source_words_set = set(norm_source.split())
    matched_words = sum(1 for w in fact_words if w in source_words_set)
    return (matched_words / len(fact_words)) >= 0.75


def find_containing_sentence(fact_text: str, sentences: List[str]) -> Optional[str]:
    """Find the original source sentence from which the fact was extracted or fragmented."""
    norm_fact = _normalize_text_for_dedup(fact_text)
    if not norm_fact:
        return None
    for sent in sentences:
        norm_sent = _normalize_text_for_dedup(sent)
        if norm_fact in norm_sent:
            return sent
    return None


def merge_and_repair_facts(raw_facts: List[Any], source_text: str) -> List[Dict[str, Any]]:
    """Fact Merge & Repair Step.
    
    If two consecutive extracted facts are fragments belonging to the same original
    source sentence/proposition (e.g. 'AI is changing the way students learn' and
    'teachers teach.'), merges them into one complete, coherent grammatical fact.
    """
    sentences = split_into_sentences(source_text)
    normalized_items: List[Dict[str, Any]] = []

    for item in raw_facts:
        if isinstance(item, dict):
            stmt = (item.get("statement") or item.get("text") or item.get("value") or "").strip()
            quote = (item.get("quote") or (item.get("source") or {}).get("quote") if isinstance(item.get("source"), dict) else None) or stmt
            page_no = int((item.get("source") or {}).get("page") if isinstance(item.get("source"), dict) else (item.get("page") or 0))
            f_type = item.get("type") or classify_fact_type(stmt)
            conf = float(item.get("confidence", 0.98))
        else:
            stmt = str(item).strip()
            quote = stmt
            page_no = 0
            f_type = classify_fact_type(stmt)
            conf = 0.95

        if stmt and len(stmt) >= 5:
            normalized_items.append({
                "statement": stmt,
                "quote": quote,
                "page": page_no,
                "type": f_type,
                "confidence": conf,
            })

    if not normalized_items:
        # If no LLM facts provided, seed directly from source sentences
        return [
            {
                "statement": s,
                "quote": s,
                "page": 1,
                "type": classify_fact_type(s),
                "confidence": 0.98,
            }
            for s in sentences
        ]

    repaired_facts: List[Dict[str, Any]] = []
    i = 0
    while i < len(normalized_items):
        curr = normalized_items[i]
        curr_stmt = curr["statement"].strip()

        # Check if current fact is a fragment or if it shares a containing sentence with the next fact
        matched_sent = find_containing_sentence(curr_stmt, sentences)

        # Check if next item came from the same sentence
        merged = False
        if i + 1 < len(normalized_items) and matched_sent:
            next_item = normalized_items[i + 1]
            next_stmt = next_item["statement"].strip()
            next_matched_sent = find_containing_sentence(next_stmt, sentences)

            # Both fragments belong to the same source sentence
            if next_matched_sent and next_matched_sent == matched_sent and next_matched_sent != next_stmt:
                # Merge into the full source sentence
                curr["statement"] = matched_sent
                curr["quote"] = matched_sent
                curr["confidence"] = max(curr["confidence"], next_item["confidence"])
                curr["type"] = classify_fact_type(matched_sent)
                repaired_facts.append(curr)
                i += 2
                merged = True
            else:
                is_independent = any(_normalize_text_for_dedup(s) == _normalize_text_for_dedup(next_stmt) for s in sentences)
                if not is_independent and (_FRAGMENT_START_RE.match(next_stmt) or (next_stmt and next_stmt[0].islower())):
                    # Next item is a dangling clause fragment
                    repaired_stmt = f"{curr_stmt.rstrip('.')} {next_stmt}".strip()
                    if not repaired_stmt.endswith("."):
                        repaired_stmt += "."
                    curr["statement"] = repaired_stmt
                    curr["quote"] = matched_sent or repaired_stmt
                    curr["type"] = classify_fact_type(repaired_stmt)
                    repaired_facts.append(curr)
                    i += 2
                    merged = True

        if not merged:
            # If current statement is an incomplete fragment of a known sentence, restore full sentence
            if matched_sent and len(curr_stmt) < len(matched_sent) * 0.7 and not curr_stmt.endswith("."):
                curr["statement"] = matched_sent
                curr["quote"] = matched_sent
                curr["type"] = classify_fact_type(matched_sent)

            # Strip leading orphaned conjunctions
            cleaned_stmt = _FRAGMENT_START_RE.sub("", curr["statement"]).strip()
            if cleaned_stmt and cleaned_stmt[0].islower():
                cleaned_stmt = cleaned_stmt[0].upper() + cleaned_stmt[1:]
            if cleaned_stmt and not cleaned_stmt.endswith((".", "!", "?")):
                cleaned_stmt += "."
            curr["statement"] = cleaned_stmt or curr["statement"]
            repaired_facts.append(curr)
            i += 1

    return repaired_facts


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
    source_text: Optional[str] = None,
) -> Tuple[List[Fact], List[str]]:
    """Deduplicates facts, repairs sentence boundaries, and attaches precise grounded references."""
    full_text = source_text or " ".join(page_texts.values())
    repaired_raw_facts = merge_and_repair_facts(raw_facts, full_text)

    seen_hashes: Set[str] = set()
    facts: List[Fact] = []
    dropped_dupes: List[str] = []

    for i, item in enumerate(repaired_raw_facts):
        stmt = (item.get("statement") or item.get("text") or item.get("value") or "").strip()
        quote = (item.get("quote") or (item.get("source") or {}).get("quote") if isinstance(item.get("source"), dict) else None) or stmt
        src_loc = item.get("source") if isinstance(item.get("source"), dict) else {}
        page_no = int(src_loc.get("page") or item.get("page") or 0)
        conf = float(item.get("confidence", 0.98))
        fact_type = item.get("type") or classify_fact_type(stmt)

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
