"""DocLink fact extraction (Phase 4).

Pipeline position::

    ExtractedDocument -> chunk -> [this module] -> facts (SPO triples) with evidence

Two cooperating strategies:

* **LLM strategy** — structured JSON prompt routed through ``DocLinkLLM``.
* **Deterministic strategy** — sentence-level subject-verb-object (SVO) and
  pattern-based parsing that always runs when no model is available.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import prompts
from .model_interface import DocLinkLLM
from .normalizer import normalize_surface, surface_key
from .schemas import FactType, RawFact
from .validator import classify_fact_type, validate_raw_facts

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])")

# Patterns for deterministic triple extraction
SVO_PATTERN = re.compile(
    r"\b([A-Z0-9][A-Za-z0-9_.\-'\s]{1,40}?)\s+"
    r"(announced|announces|released|releases|launched|launches|unveiled|unveils|developed|develops|"
    r"created|creates|built|builds|partnered|partners|acquired|acquires|detected|detects|"
    r"exploited|exploits|uses|utilizes|deployed|deploys|reported|reports)\s+"
    r"([A-Za-z0-9_.\-'\s]{2,60}?)(?=[.,;]|in\s+\d{4}|on\s+\d|by\s+|$)",
    re.I,
)

EXPLOIT_PATTERN = re.compile(
    r"(The attack|The exploit|The threat actor|The campaign)\s+exploited\s+(CVE-\d{4}-\d{4,7}|[A-Za-z0-9_\- ]+)\s+in\s+([A-Za-z0-9_\- ]+)",
    re.I,
)

TIME_SPAN_RE = re.compile(
    r"\b(in\s+(?:19|20)\d{2}|on\s+\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+(?:19|20)\d{2}|in\s+Q[1-4]\s+(?:19|20)\d{2})\b",
    re.I,
)


def extract_facts_deterministic(chunk_text: str) -> List[RawFact]:
    """Pattern / sentence parsing factual triple extraction (always available)."""
    text = chunk_text or ""
    if not text.strip():
        return []

    facts: List[RawFact] = []
    seen_keys = set()

    for sentence in _SENT_SPLIT.split(text):
        sentence_clean = normalize_surface(sentence)
        if len(sentence_clean) < 10:
            continue

        time_val = None
        time_match = TIME_SPAN_RE.search(sentence_clean)
        if time_match:
            time_val = time_match.group(1).strip()

        # Try exploit pattern
        exp_match = EXPLOIT_PATTERN.search(sentence_clean)
        if exp_match:
            subj = exp_match.group(1).strip()
            pred = "exploited"
            obj = f"{exp_match.group(2).strip()} in {exp_match.group(3).strip()}"
            fact_key = (surface_key(subj), pred, surface_key(obj))
            if fact_key not in seen_keys:
                seen_keys.add(fact_key)
                facts.append(
                    RawFact(
                        subject=subj,
                        predicate=pred,
                        object=obj,
                        time=time_val,
                        statement=sentence_clean,
                        fact_type=FactType.RISK.value,
                        confidence=0.92,
                        quote=sentence_clean,
                    )
                )

        # Try SVO pattern
        for match in SVO_PATTERN.finditer(sentence_clean):
            subj = normalize_surface(match.group(1))
            pred = match.group(2).lower().strip()
            obj = normalize_surface(match.group(3))

            if not subj or not pred or not obj or len(subj) < 2 or len(obj) < 2:
                continue

            fact_key = (surface_key(subj), pred, surface_key(obj))
            if fact_key in seen_keys:
                continue
            seen_keys.add(fact_key)

            fact_type = classify_fact_type(sentence_clean)
            facts.append(
                RawFact(
                    subject=subj,
                    predicate=pred,
                    object=obj,
                    time=time_val,
                    statement=sentence_clean,
                    fact_type=fact_type,
                    confidence=0.88,
                    quote=sentence_clean,
                )
            )

        # Fallback: if no SVO matched but sentence is meaningful, extract whole sentence as a statement fact
        if not facts and len(sentence_clean) >= 15:
            # Try to infer subject from first capitalised word/phrase
            words = sentence_clean.split()
            subj = words[0] if words else "Document"
            pred = "states"
            obj = " ".join(words[1:]) if len(words) > 1 else sentence_clean
            fact_key = (surface_key(subj), pred, surface_key(obj[:30]))
            if fact_key not in seen_keys:
                seen_keys.add(fact_key)
                facts.append(
                    RawFact(
                        subject=subj,
                        predicate=pred,
                        object=obj,
                        time=time_val,
                        statement=sentence_clean,
                        fact_type=classify_fact_type(sentence_clean),
                        confidence=0.75,
                        quote=sentence_clean,
                    )
                )

    return facts


def extract_facts_with_llm(
    chunk_text: str,
    llm: Optional[DocLinkLLM],
    known_entities: Sequence[str] = (),
    *,
    chunk_id: str = "chunk_001",
    page: int = 1,
    section: str = "",
    max_items: int = 40,
) -> Optional[List[RawFact]]:
    """Ask the configured LLM provider for structured factual triples."""
    if llm is None or not getattr(llm, "is_available", lambda: False)():
        return None

    payload = llm.generate_json(
        prompts.FACT_SYSTEM_PROMPT,
        prompts.build_fact_prompt(chunk_text, known_entities, chunk_id, page, section, max_items),
    )
    if not payload:
        return None

    raw_items = payload.get("facts") if isinstance(payload.get("facts"), list) else None
    if raw_items is None:
        raw_items = payload if isinstance(payload, list) else []

    accepted, _rejected = validate_raw_facts(raw_items)
    return accepted


def extract_facts(
    chunk_text: str,
    known_entities: Sequence[str] = (),
    *,
    llm: Optional[DocLinkLLM] = None,
    chunk_id: str = "chunk_001",
    page: int = 1,
    section: str = "",
    use_llm: bool = True,
    max_items: int = 40,
) -> Tuple[List[RawFact], List[str], str]:
    """Extract factual triples from one chunk.

    Returns ``(facts, rejected, provider)``.
    """
    rejected: List[str] = []
    deterministic_facts = extract_facts_deterministic(chunk_text)

    llm_facts: List[RawFact] = []
    provider = "deterministic"

    if use_llm:
        llm_result = extract_facts_with_llm(
            chunk_text,
            llm,
            known_entities,
            chunk_id=chunk_id,
            page=page,
            section=section,
            max_items=max_items,
        )
        if llm_result is not None:
            llm_facts = llm_result
            provider = getattr(llm, "name", "llm")

    # Combine LLM + deterministic facts, deduplicating on (subject_key, predicate, object_key)
    combined: List[RawFact] = list(llm_facts)
    seen_keys = {
        (surface_key(f.subject), f.predicate.lower(), surface_key(f.object))
        for f in llm_facts
    }

    for fact in deterministic_facts:
        key = (surface_key(fact.subject), fact.predicate.lower(), surface_key(fact.object))
        if key not in seen_keys:
            seen_keys.add(key)
            combined.append(fact)

    accepted, raw_rejected = validate_raw_facts(combined)
    rejected.extend(raw_rejected)
    return accepted, rejected, provider


__all__ = [
    "extract_facts",
    "extract_facts_deterministic",
    "extract_facts_with_llm",
]
