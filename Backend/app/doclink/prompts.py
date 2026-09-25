"""DocLink (Phase 4) prompt templates.

All prompts force **strict JSON** output — the model must never return prose.
Every returned item must carry a verbatim quote so DocLink can attach evidence.

The prompt text is provider-agnostic: prompts are handed to whatever
``DocLinkLLM`` implementation is configured (Ollama, Gemini, or a future
PyTorch model in Phase 9).
"""
from __future__ import annotations

from typing import Iterable

from .schemas import EntityType, RelationType

ENTITY_TYPES_HINT = ", ".join(t.value for t in EntityType)
RELATION_TYPES_HINT = ", ".join(r.value for r in RelationType)

_JSON_RULES = (
    "RULES:\n"
    "1. Return STRICT JSON only. No markdown, no commentary, no trailing text.\n"
    "2. Never invent facts, numbers, names or dates that are not in the text.\n"
    "3. Every item must include a verbatim 'quote' copied from the text.\n"
    "4. 'confidence' is a ranking signal between 0.0 and 1.0, not a probability.\n"
    "5. If nothing is found, return empty arrays.\n"
)

ENTITY_SYSTEM_PROMPT = (
    "You are DocLink, a precise information-extraction engine inside a document-intelligence "
    "pipeline. You extract named entities from a document chunk.\n\n"
    f"Allowed entity types: {ENTITY_TYPES_HINT}.\n"
    "Use only these types. Do not invent new types.\n\n"
    "JSON schema:\n"
    '{"entities": [{"text": "...", "canonical_name": "...", "type": "ORGANIZATION", '
    '"aliases": ["..."], "confidence": 0.0, "quote": "..."}]}\n\n' + _JSON_RULES
)

FACT_SYSTEM_PROMPT = (
    "You are DocLink, a precise factual-statement extraction engine.\n"
    "Break each meaningful statement into a subject–predicate–object triple with an optional time.\n\n"
    "JSON schema:\n"
    '{"facts": [{"subject": "...", "predicate": "...", "object": "...", "time": null, '
    '"statement": "verbatim sentence", "fact_type": "STATEMENT", "confidence": 0.0, '
    '"quote": "..."}]}\n'
    "Allowed fact_type values: STATEMENT, EVENT, MEASUREMENT, ANNOUNCEMENT, ACTION, RISK, DEFINITION.\n"
    "The predicate must be the verb phrase as written (e.g. 'announced', 'released', 'uses').\n\n"
    + _JSON_RULES
)

RELATION_SYSTEM_PROMPT = (
    "You are DocLink, a relation-extraction engine that links entities already found in the text.\n\n"
    f"Allowed relation types: {RELATION_TYPES_HINT}.\n"
    "You must map every relation to one of these types. Never invent a new relation type. "
    "If the text expresses a connection that fits no specific type, use RELATED_TO.\n\n"
    "JSON schema:\n"
    '{"relations": [{"source": "entity surface form", "relation": "PARTNERED_WITH", '
    '"target": "entity surface form", "confidence": 0.0, "quote": "..."}]}\n'
    "Do not relate an entity to itself, and do not invent entities.\n\n" + _JSON_RULES
)

COMBINED_SYSTEM_PROMPT = (
    "You are DocLink, the entity / fact / relation extraction engine of a document-intelligence "
    "pipeline. You receive one document chunk and return entities, factual triples and relations "
    "between those entities.\n\n"
    f"Allowed entity types: {ENTITY_TYPES_HINT}.\n"
    f"Allowed relation types: {RELATION_TYPES_HINT}.\n\n"
    "JSON schema:\n"
    "{\n"
    '  "entities": [{"text": "...", "canonical_name": "...", "type": "ORGANIZATION", "aliases": [], "confidence": 0.0, "quote": "..."}],\n'
    '  "facts": [{"subject": "...", "predicate": "...", "object": "...", "time": null, "statement": "...", "fact_type": "STATEMENT", "confidence": 0.0, "quote": "..."}],\n'
    '  "relations": [{"source": "...", "relation": "DEVELOPED", "target": "...", "confidence": 0.0, "quote": "..."}]\n'
    "}\n\n" + _JSON_RULES
)


def _chunk_header(chunk_id: str, page: int = 1, section: str = "") -> str:
    header = f"CHUNK_ID: {chunk_id}\nPAGE: {page}\n"
    if section:
        header += f"SECTION: {section}\n"
    return header


def build_entity_prompt(chunk_text: str, chunk_id: str = "chunk_001", page: int = 1,
                        section: str = "", max_items: int = 40) -> str:
    return (
        f"{_chunk_header(chunk_id, page, section)}"
        f"Extract at most {max_items} entities.\n\nTEXT:\n{chunk_text}"
    )


def build_fact_prompt(chunk_text: str, entities: Iterable[str] = (), chunk_id: str = "chunk_001",
                      page: int = 1, section: str = "", max_items: int = 40) -> str:
    known = [e for e in entities if e][:40]
    known_block = ("Known entities (prefer these as subject/object where applicable): "
                   + ", ".join(known) + "\n") if known else ""
    return (
        f"{_chunk_header(chunk_id, page, section)}"
        f"{known_block}Extract at most {max_items} factual triples.\n\nTEXT:\n{chunk_text}"
    )


def build_relation_prompt(chunk_text: str, entities: Iterable[str] = (), chunk_id: str = "chunk_001",
                          page: int = 1, section: str = "", max_items: int = 40) -> str:
    known = [e for e in entities if e][:40]
    known_block = ("Known entities (source/target MUST be one of these): "
                   + ", ".join(known) + "\n") if known else ""
    return (
        f"{_chunk_header(chunk_id, page, section)}"
        f"{known_block}Extract at most {max_items} relations.\n\nTEXT:\n{chunk_text}"
    )


def build_combined_prompt(chunk_text: str, chunk_id: str = "chunk_001", page: int = 1,
                          section: str = "", max_items: int = 40) -> str:
    return (
        f"{_chunk_header(chunk_id, page, section)}"
        f"Extract at most {max_items} entities, {max_items} facts and {max_items} relations.\n\n"
        f"TEXT:\n{chunk_text}"
    )


def prompt_for_stage(stage: str, chunk_text: str, entities: Iterable[str] = (), *,
                     chunk_id: str = "chunk_001", page: int = 1, section: str = "",
                     max_items: int = 40) -> str:
    """Dispatch helper shared by the extractors."""
    stage = (stage or "combined").lower()
    if stage == "entities":
        return build_entity_prompt(chunk_text, chunk_id, page, section, max_items)
    if stage == "facts":
        return build_fact_prompt(chunk_text, entities, chunk_id, page, section, max_items)
    if stage == "relations":
        return build_relation_prompt(chunk_text, entities, chunk_id, page, section, max_items)
    return build_combined_prompt(chunk_text, chunk_id, page, section, max_items)


__all__ = [
    "ENTITY_TYPES_HINT",
    "RELATION_TYPES_HINT",
    "ENTITY_SYSTEM_PROMPT",
    "FACT_SYSTEM_PROMPT",
    "RELATION_SYSTEM_PROMPT",
    "COMBINED_SYSTEM_PROMPT",
    "build_entity_prompt",
    "build_fact_prompt",
    "build_relation_prompt",
    "build_combined_prompt",
    "prompt_for_stage",
]

