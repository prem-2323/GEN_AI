"""DocLink relation extraction (Phase 4).

Pipeline position::

    ExtractedDocument -> chunk -> [this module] -> relations connecting entities with evidence

Two cooperating strategies:

* **LLM strategy** — structured JSON prompt routed through ``DocLinkLLM``.
* **Deterministic strategy** — pattern & co-occurrence based relation matching
  between known entities.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import prompts
from .model_interface import DocLinkLLM
from .normalizer import normalize_surface, surface_key
from .schemas import (
    RELATION_TYPE_ALIASES,
    RawEntity,
    RawRelation,
    RelationType,
    normalize_relation_type,
)
from .validator import validate_raw_relations

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])")

# Relation verb / phrase matching rules
RELATION_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\b(partnered\s+with|partners\s+with|collaborated\s+with|in\s+partnership\s+with)\b", re.I), "PARTNERED_WITH"),
    (re.compile(r"\b(developed|develops|building|built|engineered|designed)\b", re.I), "DEVELOPED"),
    (re.compile(r"\b(released|releases|published|publishes|launched|launches|unveiled|unveils|produced|produces)\b", re.I), "PRODUCED"),
    (re.compile(r"\b(announced|announces|declared|declares|reported|reports|introduced)\b", re.I), "ANNOUNCED"),
    (re.compile(r"\b(uses|utilizes|utilises|leverages|relying\s+on|relies\s+on|depends\s+on)\b", re.I), "USES"),
    (re.compile(r"\b(acquired|acquires|owns|purchased|bought)\b", re.I), "OWNS"),
    (re.compile(r"\b(located\s+in|headquartered\s+in|based\s+in)\b", re.I), "LOCATED_IN"),
    (re.compile(r"\b(works\s+for|employed\s+by|ceo\s+of|cto\s+of|founder\s+of|director\s+of)\b", re.I), "WORKS_FOR"),
    (re.compile(r"\b(part\s+of|division\s+of|subsidiary\s+of|unit\s+of)\b", re.I), "PART_OF"),
    (re.compile(r"\b(created|founded|established|instituted)\b", re.I), "CREATED"),
    (re.compile(r"\b(exploited|exploited\s+in|affects|targeting|targeted)\b", re.I), "APPLIES_TO"),
    (re.compile(r"\b(occurred\s+on|happened\s+on|dated)\b", re.I), "OCCURRED_ON"),
    (re.compile(r"\b(mentions|references|cites)\b", re.I), "MENTIONS"),
]


def extract_relations_deterministic(
    chunk_text: str,
    known_entities: Sequence[RawEntity] = (),
) -> List[RawRelation]:
    """Pattern and entity co-occurrence relation extraction (always available)."""
    text = chunk_text or ""
    if not text.strip() or len(known_entities) < 2:
        return []

    relations: List[RawRelation] = []
    seen_keys = set()

    # Index entity surface forms
    entities_by_surface = [e for e in known_entities if e.text and len(e.text) >= 2]

    for sentence in _SENT_SPLIT.split(text):
        sent_clean = normalize_surface(sentence)
        if not sent_clean:
            continue
        sent_lower = sent_clean.lower()

        # Find all entities present in this sentence
        present = []
        for entity in entities_by_surface:
            surf_key = surface_key(entity.text)
            if surf_key and surf_key in surface_key(sent_clean):
                pos = sent_lower.find(entity.text.lower())
                present.append((pos if pos >= 0 else 0, entity))

        if len(present) < 2:
            continue

        # Sort present entities by appearance order in sentence
        present.sort(key=lambda x: x[0])

        for i in range(len(present)):
            for j in range(i + 1, len(present)):
                ent1 = present[i][1]
                ent2 = present[j][1]

                # Don't relate entity to itself
                if surface_key(ent1.text) == surface_key(ent2.text):
                    continue

                # Search span between ent1 and ent2
                p1 = sent_lower.find(ent1.text.lower())
                p2 = sent_lower.find(ent2.text.lower())

                if p1 < 0 or p2 < 0:
                    continue

                start_idx, end_idx = min(p1, p2), max(p1, p2)
                between_text = sent_clean[start_idx:end_idx + len(ent2.text)]

                matched_rel = None
                for pat, rel_type in RELATION_PATTERNS:
                    if pat.search(between_text):
                        matched_rel = rel_type
                        break

                if not matched_rel:
                    # Fallback relation if co-occurring in same sentence
                    matched_rel = RelationType.RELATED_TO.value

                rel_key = (surface_key(ent1.text), matched_rel, surface_key(ent2.text))
                if rel_key not in seen_keys:
                    seen_keys.add(rel_key)
                    relations.append(
                        RawRelation(
                            source=ent1.text,
                            relation=matched_rel,
                            target=ent2.text,
                            confidence=0.85 if matched_rel != "RELATED_TO" else 0.65,
                            quote=sent_clean,
                        )
                    )

    return relations


def extract_relations_with_llm(
    chunk_text: str,
    llm: Optional[DocLinkLLM],
    known_entities: Sequence[str] = (),
    *,
    chunk_id: str = "chunk_001",
    page: int = 1,
    section: str = "",
    max_items: int = 40,
) -> Optional[List[RawRelation]]:
    """Ask the configured LLM provider for structured relations between entities."""
    if llm is None or not getattr(llm, "is_available", lambda: False)():
        return None

    payload = llm.generate_json(
        prompts.RELATION_SYSTEM_PROMPT,
        prompts.build_relation_prompt(chunk_text, known_entities, chunk_id, page, section, max_items),
    )
    if not payload:
        return None

    raw_items = payload.get("relations") if isinstance(payload.get("relations"), list) else None
    if raw_items is None:
        raw_items = payload if isinstance(payload, list) else []

    accepted, _warn, _rejected = validate_raw_relations(raw_items)
    return accepted


def extract_relations(
    chunk_text: str,
    known_entities: Sequence[RawEntity] = (),
    *,
    llm: Optional[DocLinkLLM] = None,
    chunk_id: str = "chunk_001",
    page: int = 1,
    section: str = "",
    use_llm: bool = True,
    max_items: int = 40,
) -> Tuple[List[RawRelation], List[str], str]:
    """Extract relations connecting entities from one chunk.

    Returns ``(relations, rejected, provider)``.
    """
    rejected: List[str] = []
    deterministic_relations = extract_relations_deterministic(chunk_text, known_entities)

    llm_relations: List[RawRelation] = []
    provider = "deterministic"

    entity_names = [e.text for e in known_entities if e.text]

    if use_llm:
        llm_result = extract_relations_with_llm(
            chunk_text,
            llm,
            entity_names,
            chunk_id=chunk_id,
            page=page,
            section=section,
            max_items=max_items,
        )
        if llm_result is not None:
            llm_relations = llm_result
            provider = getattr(llm, "name", "llm")

    # Combine LLM + deterministic relations
    combined: List[RawRelation] = list(llm_relations)
    seen_keys = {
        (surface_key(r.source), normalize_relation_type(r.relation), surface_key(r.target))
        for r in llm_relations
    }

    for rel in deterministic_relations:
        key = (surface_key(rel.source), normalize_relation_type(rel.relation), surface_key(rel.target))
        if key not in seen_keys:
            seen_keys.add(key)
            combined.append(rel)

    accepted, _warn, raw_rejected = validate_raw_relations(combined)
    rejected.extend(raw_rejected)
    return accepted, rejected, provider


__all__ = [
    "extract_relations",
    "extract_relations_deterministic",
    "extract_relations_with_llm",
]
