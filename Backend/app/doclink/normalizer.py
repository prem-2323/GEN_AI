"""DocLink normalizer — canonicalisation, deduplication, coreference and merging.

Responsibilities:

* Case / whitespace / punctuation normalisation of surface forms.
* Entity clustering: ``OpenAI`` = ``Open AI`` = ``OpenAI Inc.`` (confidence-based,
  never a blind merge — merges are confidence-weighted and logged).
* Entity index so facts and relations can be re-pointed at ``entity_id`` values.
* Duplicate fact / relation removal.
* Conservative pronoun & definite-description coreference (``the company`` ->
  ``OpenAI``) so chunk-local mentions can be merged across chunks.
* Cross-chunk merge entry point (``merge_chunk_results``).
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .schemas import (
    ChunkExtraction,
    DocLinkEntity,
    DocLinkFact,
    DocLinkRelation,
    EntityType,
    RawEntity,
    RawFact,
    RawRelation,
    SourceSpan,
)

_WS_RE = re.compile(r"\s+")
_PUNCT_EDGE_RE = re.compile(r"^[\s\"'“”‘’`(\[\{<>,;:.\-–—_|/\\]+|[\s\"'“”‘’`)\]\}>.,;:!?\-–—_|/\\]+$")
_QUOTE_FIX_RE = re.compile(r"\s+([,.;:!?])")
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])")

_STOPWORDS = {
    "the", "this", "that", "these", "those", "with", "from", "there", "when", "where",
    "which", "and", "but", "for", "you", "your", "our", "their", "his", "her", "its",
    "it", "they", "them", "we", "us", "she", "he", "i", "a", "an",
}

LEGAL_SUFFIXES = (
    "incorporated", "corporation", "corp", "inc", "ltd", "limited", "llc", "llp", "plc",
    "gmbh", "ag", "sa", "sas", "nv", "bv", "pty", "co", "company", "holdings", "group",
)

# Definite-description / pronoun coreference cues -> compatible entity types.
COREFERENCE_CUES: Dict[str, Tuple[str, ...]] = {
    "the company": (EntityType.ORGANIZATION.value,),
    "the firm": (EntityType.ORGANIZATION.value,),
    "the organization": (EntityType.ORGANIZATION.value,),
    "the organisation": (EntityType.ORGANIZATION.value,),
    "the agency": (EntityType.ORGANIZATION.value,),
    "the vendor": (EntityType.ORGANIZATION.value,),
    "the ministry": (EntityType.ORGANIZATION.value,),
    "the university": (EntityType.ORGANIZATION.value,),
    "the institute": (EntityType.ORGANIZATION.value,),
    "the group": (EntityType.ORGANIZATION.value,),
    "the team": (EntityType.ORGANIZATION.value,),
    "the city": (EntityType.CITY.value, EntityType.LOCATION.value),
    "the country": (EntityType.COUNTRY.value, EntityType.LOCATION.value),
    "the region": (EntityType.LOCATION.value,),
    "the platform": (EntityType.TECHNOLOGY.value, EntityType.PRODUCT.value),
    "the system": (EntityType.TECHNOLOGY.value, EntityType.PRODUCT.value),
    "the tool": (EntityType.TECHNOLOGY.value, EntityType.PRODUCT.value),
    "the model": (EntityType.TECHNOLOGY.value, EntityType.PRODUCT.value),
    "the technology": (EntityType.TECHNOLOGY.value, EntityType.PRODUCT.value),
    "the product": (EntityType.PRODUCT.value, EntityType.TECHNOLOGY.value),
    "the document": (EntityType.DOCUMENT.value,),
    "the report": (EntityType.DOCUMENT.value,),
    "the policy": (EntityType.POLICY.value, EntityType.LAW.value),
    "the law": (EntityType.LAW.value,),
}
PRONOUNS = ("it", "they", "them", "this", "that")


def normalize_whitespace(text: str) -> str:
    """Collapse all whitespace runs (incl. tabs/newlines) into single spaces."""
    return _WS_RE.sub(" ", (text or "").replace("\u00a0", " ")).strip()


def normalize_surface(text: str) -> str:
    """Canonical surface form: trimmed, de-quoted, whitespace-normalised."""
    cleaned = normalize_whitespace(text)
    cleaned = _PUNCT_EDGE_RE.sub("", cleaned)
    cleaned = _QUOTE_FIX_RE.sub(r"\1", cleaned)
    return cleaned.strip()


def surface_key(text: str) -> str:
    """Dedup key: case-, whitespace- and punctuation-insensitive."""
    cleaned = normalize_surface(text).lower()
    cleaned = re.sub(r"[^\w\s]", "", cleaned)
    return normalize_whitespace(cleaned)


def cluster_key(name: str) -> str:
    """Clustering key used to merge legal-suffix / spacing / case variants."""
    cleaned = normalize_surface(name).lower()
    cleaned = re.sub(r"[^\w\s]", "", cleaned)
    tokens = [t for t in cleaned.split() if t not in LEGAL_SUFFIXES]
    if tokens and tokens[0] == "the":
        tokens = tokens[1:]
    joined = "".join(tokens)
    return joined or re.sub(r"[^\w]", "", cleaned)


def is_same_entity(a: str, b: str) -> bool:
    """Conservative similarity check used for confidence-scored merging."""
    ka, kb = cluster_key(a), cluster_key(b)
    if not ka or not kb:
        return False
    if ka == kb:
        return True
    shorter, longer = sorted((ka, kb), key=len)
    return len(shorter) >= 5 and longer.startswith(shorter) and (len(longer) - len(shorter)) <= 4


def canonical_candidate(names: Iterable[str]) -> str:
    """Pick the most informative canonical name (longest, minus legal suffixes)."""
    cleaned = [normalize_surface(n) for n in names if normalize_surface(n)]
    if not cleaned:
        return ""
    def score(value: str) -> Tuple[int, int, int]:
        has_space = 1 if " " in value else 0
        return (has_space, -abs(len(value) - 18), len(value))
    return sorted(cleaned, key=score, reverse=True)[0]


def merge_evidence(*groups: Sequence[SourceSpan]) -> List[SourceSpan]:
    """Merge evidence spans, de-duplicating on (document, chunk, page, quote)."""
    seen: Dict[tuple, SourceSpan] = {}
    for group in groups:
        for span in group or []:
            seen.setdefault(span.key(), span)
    return list(seen.values())


# ---------------------------------------------------------------------------
# Entity clustering / deduplication
# ---------------------------------------------------------------------------
def deduplicate_entities(
    entities: List[DocLinkEntity],
    *,
    min_merge_confidence: float = 0.6,
) -> Tuple[List[DocLinkEntity], Dict[str, Any]]:
    """Cluster and merge equivalent entities; returns (entities, merge_summary).

    Merging is never blind: an entity is only folded into an existing cluster when
    the cluster key matches and the resulting merge confidence is >= the
    ``min_merge_confidence`` threshold (mean of the two confidences).
    """
    clusters: List[Dict[str, Any]] = []
    merge_log: List[Dict[str, Any]] = []
    removed = 0

    for entity in entities:
        name = normalize_surface(entity.text or entity.canonical_name)
        if not name:
            continue
        entity.text = name
        entity.canonical_name = normalize_surface(entity.canonical_name or name) or name
        surface_forms = {name, entity.canonical_name}
        surface_forms.update(normalize_surface(s) for s in entity.surface_forms if s)
        surface_forms.discard("")
        entity.surface_forms = sorted(surface_forms)

        target: Optional[Dict[str, Any]] = None
        for cluster in clusters:
            keys_match = cluster_key(cluster["canonical_name"]) == cluster_key(entity.canonical_name)
            if not keys_match or cluster["type"] != entity.type:
                continue
            merged_conf = round((float(cluster["confidence"]) + float(entity.confidence)) / 2.0, 3)
            if merged_conf < min_merge_confidence:
                continue
            target = cluster
            break

        if target is None:
            clusters.append(
                {
                    "canonical_name": canonical_candidate(entity.surface_forms) or entity.canonical_name,
                    "type": entity.type,
                    "confidence": float(entity.confidence),
                    "mentions": int(entity.mentions or 1),
                    "surface_forms": set(entity.surface_forms),
                    "aliases_resolved": set(entity.aliases_resolved),
                    "evidence": merge_evidence(entity.evidence),
                }
            )
            continue

        removed += 1
        target["surface_forms"].update(entity.surface_forms)
        target["aliases_resolved"].update(entity.aliases_resolved)
        target["mentions"] += int(entity.mentions or 1)
        target["confidence"] = max(float(target["confidence"]), float(entity.confidence))
        target["canonical_name"] = (
            canonical_candidate(target["surface_forms"]) or target["canonical_name"]
        )
        target["evidence"] = merge_evidence(target["evidence"], entity.evidence)
        merge_log.append(
            {
                "canonical_name": target["canonical_name"],
                "merged": sorted(entity.surface_forms),
                "type": entity.type,
            }
        )

    merged: List[DocLinkEntity] = []
    for idx, cluster in enumerate(clusters, start=1):
        canonical = cluster["canonical_name"]
        forms = sorted(cluster["surface_forms"] - {canonical})
        merged.append(
            DocLinkEntity(
                entity_id=f"ent_{idx:03d}",
                text=canonical,
                canonical_name=canonical,
                surface_forms=forms,
                type=cluster["type"],
                confidence=round(float(cluster["confidence"]), 3),
                mentions=int(cluster["mentions"]),
                evidence=cluster["evidence"],
                aliases_resolved=sorted(cluster["aliases_resolved"]),
            )
        )

    merged, dropped = apply_type_voting(merged)
    removed += dropped
    summary = {
        "mergedEntities": len(merged),
        "duplicateEntitiesRemoved": removed,
        "mergeLog": merge_log,
    }
    return merged, summary



def apply_type_voting(entities: List[DocLinkEntity]) -> Tuple[List[DocLinkEntity], int]:
    """Safety net: re-merge entities that ended up with different types."""
    kept: List[DocLinkEntity] = []
    dropped = 0
    for entity in entities:
        duplicate = next(
            (
                k for k in kept
                if cluster_key(k.canonical_name) == cluster_key(entity.canonical_name)
            ),
            None,
        )
        if duplicate is None:
            kept.append(entity)
            continue
        duplicate.surface_forms = sorted(
            set(duplicate.surface_forms) | set(entity.surface_forms) | {entity.canonical_name}
        )
        duplicate.mentions += entity.mentions
        duplicate.confidence = max(duplicate.confidence, entity.confidence)
        duplicate.evidence = merge_evidence(duplicate.evidence, entity.evidence)
        duplicate.type = _dominant_type(duplicate.type, entity.type)
        dropped += 1
    for idx, entity in enumerate(kept, start=1):
        entity.entity_id = f"ent_{idx:03d}"
    return kept, dropped


_TYPE_PRIORITY = {
    EntityType.ORGANIZATION.value: 6,
    EntityType.PERSON.value: 6,
    EntityType.PRODUCT.value: 5,
    EntityType.TECHNOLOGY.value: 5,
    EntityType.COUNTRY.value: 4,
    EntityType.CITY.value: 4,
    EntityType.LOCATION.value: 3,
    EntityType.EVENT.value: 3,
    EntityType.LAW.value: 3,
    EntityType.POLICY.value: 3,
    EntityType.DOCUMENT.value: 2,
    EntityType.IDENTIFIER.value: 2,
    EntityType.DATE.value: 1,
    EntityType.TIME.value: 1,
    EntityType.AMOUNT.value: 1,
}


def _dominant_type(a: str, b: str) -> str:
    return a if _TYPE_PRIORITY.get(a, 0) >= _TYPE_PRIORITY.get(b, 0) else b


def build_entity_index(entities: Sequence[DocLinkEntity]) -> Dict[str, str]:
    """Map every surface form / canonical name / resolved alias to an entity_id."""
    index: Dict[str, str] = {}
    for entity in entities:
        for candidate in [entity.canonical_name, entity.text, *entity.surface_forms, *entity.aliases_resolved]:
            key = surface_key(candidate)
            if key:
                index.setdefault(key, entity.entity_id)
        ckey = cluster_key(entity.canonical_name)
        if ckey:
            index.setdefault(ckey, entity.entity_id)
    return index


def link_entity_reference(name: str, index: Dict[str, str]) -> Optional[str]:
    """Resolve a free-text mention to an ``entity_id`` (surface key or cluster key)."""
    if not name:
        return None
    direct = index.get(surface_key(name))
    if direct:
        return direct
    return index.get(cluster_key(name))



def deduplicate_facts(facts: List[DocLinkFact]) -> Tuple[List[DocLinkFact], int]:
    """Remove duplicate triples and duplicate statements; reassign fact ids."""
    seen_triples: set = set()
    seen_statements: set = set()
    kept: List[DocLinkFact] = []
    removed = 0
    for fact in facts:
        triple = (
            surface_key(fact.subject),
            surface_key(fact.predicate),
            surface_key(fact.object),
            surface_key(fact.time or ""),
        )
        statement_key = surface_key(fact.statement)
        if triple in seen_triples or (statement_key and statement_key in seen_statements):
            removed += 1
            continue
        seen_triples.add(triple)
        if statement_key:
            seen_statements.add(statement_key)
        fact.fact_id = f"fact_{len(kept) + 1:03d}"
        kept.append(fact)
    return kept, removed


def deduplicate_relations(relations: List[DocLinkRelation]) -> Tuple[List[DocLinkRelation], int]:
    """Remove duplicate / self-referencing relations; reassign relation ids."""
    seen: set = set()
    kept: List[DocLinkRelation] = []
    removed = 0
    for relation in relations:
        if surface_key(relation.source) == surface_key(relation.target):
            removed += 1
            continue
        rel_key = (surface_key(relation.source), relation.relation, surface_key(relation.target))
        if rel_key in seen:
            removed += 1
            continue
        seen.add(rel_key)
        relation.relation_id = f"rel_{len(kept) + 1:03d}"
        kept.append(relation)
    return kept, removed


def canonicalize_references(
    facts: List[DocLinkFact],
    relations: List[DocLinkRelation],
    entities: Sequence[DocLinkEntity],
) -> Dict[str, int]:
    """Re-point fact/relation mentions at canonical entity names + ``entity_id``s."""
    index = build_entity_index(entities)
    names_by_id = {e.entity_id: e.canonical_name for e in entities}
    linked = 0

    for fact in facts:
        subject_id = link_entity_reference(fact.subject, index)
        object_id = link_entity_reference(fact.object, index)
        if subject_id:
            fact.subject_id = subject_id
            fact.subject = names_by_id.get(subject_id, fact.subject)
            linked += 1
        if object_id:
            fact.object_id = object_id
            fact.object = names_by_id.get(object_id, fact.object)
            linked += 1

    for relation in relations:
        source_id = link_entity_reference(relation.source, index)
        target_id = link_entity_reference(relation.target, index)
        if source_id:
            relation.source_id = source_id
            relation.source = names_by_id.get(source_id, relation.source)
        if target_id:
            relation.target_id = target_id
            relation.target = names_by_id.get(target_id, relation.target)
        if source_id and target_id:
            linked += 1

    return {"linkedReferences": linked, "indexedSurfaces": len(index)}



def resolve_coreferences(entities: List[DocLinkEntity], chunk_text: str) -> List[str]:
    """Attach conservative coreference aliases (``the company`` -> ``OpenAI``).

    Only cue phrases with exactly one compatible entity present in the chunk are
    resolved, so an ambiguous document never produces a speculative merge.
    """
    notes: List[str] = []
    if not entities or not chunk_text:
        return notes
    lowered = chunk_text.lower()
    by_type: Dict[str, List[DocLinkEntity]] = {}
    for entity in entities:
        by_type.setdefault(entity.type, []).append(entity)

    for cue, compatible_types in COREFERENCE_CUES.items():
        if not re.search(rf"\b{re.escape(cue)}\b", lowered):
            continue
        candidates: List[DocLinkEntity] = []
        for entity_type in compatible_types:
            candidates.extend(by_type.get(entity_type, []))
        unique = {e.entity_id: e for e in candidates}
        if len(unique) != 1:
            continue
        entity = next(iter(unique.values()))
        if cue not in entity.aliases_resolved:
            entity.aliases_resolved.append(cue)
            if cue not in entity.surface_forms:
                entity.surface_forms.append(cue)
            notes.append(f"{cue} -> {entity.canonical_name}")

    matched_pronoun = next((p for p in PRONOUNS if re.search(rf"\b{p}\b", lowered)), "")
    if matched_pronoun:
        for entity_type in (EntityType.ORGANIZATION.value, EntityType.PERSON.value):
            unique = {e.entity_id: e for e in by_type.get(entity_type, [])}
            if len(unique) == 1:
                entity = next(iter(unique.values()))
                entity.confidence = round(max(0.0, entity.confidence - 0.02), 3)
                notes.append(f"pronoun '{matched_pronoun}' may refer to {entity.canonical_name}")
                break
    return notes


def merge_chunk_results(chunk_extractions: Sequence[ChunkExtraction]) -> Dict[str, Any]:
    """Flatten per-chunk raw extraction results for global (cross-chunk) merging."""
    entities: List[RawEntity] = []
    facts: List[RawFact] = []
    relations: List[RawRelation] = []
    rejected: List[str] = []
    for chunk in chunk_extractions:
        entities.extend(chunk.entities)
        facts.extend(chunk.facts)
        relations.extend(chunk.relations)
        rejected.extend(chunk.rejected)
    return {
        "entities": entities,
        "facts": facts,
        "relations": relations,
        "rejected": rejected,
        "chunkCount": len(chunk_extractions),
    }


def evidence_coverage(*collections: Iterable[Any]) -> float:
    """Percentage of entities/facts/relations that carry at least one evidence span."""
    total = 0
    grounded = 0
    for collection in collections:
        for item in collection:
            total += 1
            if getattr(item, "evidence", None):
                grounded += 1
    return round((grounded / total) * 100.0, 1) if total else 100.0


__all__ = [
    "LEGAL_SUFFIXES",
    "COREFERENCE_CUES",
    "normalize_whitespace",
    "normalize_surface",
    "surface_key",
    "cluster_key",
    "is_same_entity",
    "canonical_candidate",
    "merge_evidence",
    "deduplicate_entities",
    "apply_type_voting",
    "build_entity_index",
    "link_entity_reference",
    "deduplicate_facts",
    "deduplicate_relations",
    "canonicalize_references",
    "resolve_coreferences",
    "merge_chunk_results",
    "evidence_coverage",
]

