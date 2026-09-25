"""DocLink validator — strict validation of model output and of the final result.

Two layers:

1. **Raw validation** — every item produced by an LLM or the deterministic
   extractors is coerced into a typed ``Raw*`` object, then accepted or rejected.
   Invalid entity types, empty entity names, missing fact subjects/predicates,
   missing relation sources/targets and self-relations are rejected here.
2. **Result validation** — ``validate_doclink_result`` audits the assembled
   ``DocLinkResult`` for unique ids, valid controlled types, resolvable relation
   endpoints, fact shape and evidence coverage.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from .normalizer import (
    build_entity_index,
    cluster_key,
    evidence_coverage,
    link_entity_reference,
    normalize_surface,
    surface_key,
)
from .schemas import (
    DocLinkEntity,
    DocLinkFact,
    DocLinkRelation,
    DocLinkResult,
    DocLinkValidationReport,
    FactType,
    RawEntity,
    RawFact,
    RawRelation,
    RelationType,
    SourceSpan,
    is_valid_entity_type,
    normalize_entity_type,
    normalize_relation_type,
)

MAX_ENTITY_TEXT_LENGTH = 120
MIN_ENTITY_TEXT_LENGTH = 2
MIN_FACT_STATEMENT_LENGTH = 8
MAX_PREDICATE_LENGTH = 60

_STOPWORD_SURFACES = {
    "the", "a", "an", "this", "that", "these", "those", "it", "they", "them",
    "he", "she", "we", "you", "i", "and", "or", "but", "if", "then", "than",
}

_RISK_RE = re.compile(
    r"\b(risk|threat|vulnerab|attack|breach|critical|fail|loss|expos|malware|phishing|ransomware|cve)\b",
    re.I,
)
_ACTION_RE = re.compile(
    r"\b(must|should|shall|need to|needs to|ensure|implement|deploy|update|patch|enforce|migrate|rotate|isolate|reset)\b",
    re.I,
)
_ANNOUNCE_RE = re.compile(
    r"\b(announc|unveil|reveal|launch|introduc|declar|reported|plans to)\b", re.I
)
_MEASURE_RE = re.compile(
    r"(\d+[\.,]?\d*\s*(%|percent|million|billion|thousand|km|ms|mb|gb|tb|days?|hours?|minutes?|seconds?|users?|systems?|records?))|\b\d{2,}\b",
    re.I,
)
_DATE_RE = re.compile(
    r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{4}|\b(19|20)\d{2}\b)\b",
    re.I,
)
_DEFINITION_RE = re.compile(r"\b(is a|is an|refers to|means|is defined as|is known as)\b", re.I)


def classify_fact_type(statement: str) -> str:
    """Deterministic fact-type classification (used when no type is supplied)."""
    text = statement or ""
    if _RISK_RE.search(text):
        return FactType.RISK.value
    if _ACTION_RE.search(text):
        return FactType.ACTION.value
    if _ANNOUNCE_RE.search(text):
        return FactType.ANNOUNCEMENT.value
    if _MEASURE_RE.search(text):
        return FactType.MEASUREMENT.value
    if _DATE_RE.search(text):
        return FactType.EVENT.value
    if _DEFINITION_RE.search(text):
        return FactType.DEFINITION.value
    return FactType.STATEMENT.value


def _as_dict(item: Any) -> Dict[str, Any]:
    if isinstance(item, dict):
        return item
    if hasattr(item, "model_dump"):
        return item.model_dump()
    return {"text": str(item)}


def validate_raw_entities(raw_items: Iterable[Any]) -> Tuple[List[RawEntity], List[str]]:
    """Coerce + validate raw entity candidates; invalid candidates are rejected."""
    accepted: List[RawEntity] = []
    rejected: List[str] = []
    for item in raw_items or []:
        data = _as_dict(item)
        text = normalize_surface(str(data.get("text") or data.get("name") or data.get("entity") or ""))
        if len(text) < MIN_ENTITY_TEXT_LENGTH:
            rejected.append(f"Entity rejected (name too short): '{text}'")
            continue
        if len(text) > MAX_ENTITY_TEXT_LENGTH:
            rejected.append(f"Entity rejected (name too long): '{text[:40]}...'")
            continue
        if surface_key(text) in _STOPWORD_SURFACES:
            rejected.append(f"Entity rejected (stopword): '{text}'")
            continue
        entity_type = normalize_entity_type(data.get("type") or data.get("entity_type"))
        if not is_valid_entity_type(entity_type):
            rejected.append(f"Entity rejected (invalid type '{data.get('type')}'): '{text}'")
            continue
        aliases = [normalize_surface(str(a)) for a in (data.get("aliases") or []) if normalize_surface(str(a))]
        accepted.append(
            RawEntity(
                text=text,
                name=text,
                type=entity_type,
                canonical_name=normalize_surface(str(data.get("canonical_name") or text)) or text,
                confidence=data.get("confidence"),
                role=data.get("role"),
                aliases=aliases,
                quote=str(data.get("quote") or ""),
            )
        )
    return accepted, rejected


def validate_raw_facts(raw_items: Iterable[Any]) -> Tuple[List[RawFact], List[str]]:
    """Coerce + validate raw factual triples; missing subject/predicate is rejected."""
    accepted: List[RawFact] = []
    rejected: List[str] = []
    for item in raw_items or []:
        data = _as_dict(item)
        subject = normalize_surface(str(data.get("subject") or ""))
        predicate = normalize_surface(str(data.get("predicate") or ""))
        obj = normalize_surface(str(data.get("object") or ""))
        statement = normalize_surface(str(data.get("statement") or data.get("quote") or ""))

        if not subject:
            rejected.append(f"Fact rejected (missing subject): '{statement[:60]}'")
            continue
        if not predicate:
            rejected.append(f"Fact rejected (missing predicate): '{statement[:60]}'")
            continue
        if not statement:
            statement = f"{subject} {predicate} {obj}".strip()
        if len(statement) < MIN_FACT_STATEMENT_LENGTH:
            rejected.append(f"Fact rejected (statement too short): '{statement}'")
            continue
        if len(predicate) > MAX_PREDICATE_LENGTH:
            predicate = " ".join(predicate.split()[:6])

        fact_type = str(data.get("fact_type") or "").strip().upper()
        if fact_type not in FactType.__members__:
            fact_type = classify_fact_type(statement)

        time_value = data.get("time") or data.get("date") or None
        accepted.append(
            RawFact(
                subject=subject,
                predicate=predicate,
                object=obj,
                time=normalize_surface(str(time_value)) if time_value else None,
                statement=statement,
                fact_type=fact_type,
                confidence=data.get("confidence"),
                quote=str(data.get("quote") or statement),
            )
        )
    return accepted, rejected


def validate_raw_relations(
    raw_items: Iterable[Any],
    known_entities: Sequence[str] = (),
) -> Tuple[List[RawRelation], List[str], List[str]]:
    """Coerce + validate raw relations. Returns (relations, warnings, rejected)."""
    accepted: List[RawRelation] = []
    warnings: List[str] = []
    rejected: List[str] = []
    known_keys = {surface_key(n): n for n in known_entities if n}
    known_keys.update({cluster_key(n): n for n in known_entities if n})

    for item in raw_items or []:
        data = _as_dict(item)
        source = normalize_surface(str(data.get("source") or ""))
        target = normalize_surface(str(data.get("target") or ""))
        relation = str(data.get("relation") or "").strip()

        if not source:
            rejected.append(f"Relation rejected (missing source): --{relation or '?'}--> {target or '?'}")
            continue
        if not target:
            rejected.append(f"Relation rejected (missing target): {source} --{relation or '?'}--> --")
            continue
        if surface_key(source) == surface_key(target):
            rejected.append(f"Relation rejected (self-relation): {source}")
            continue
        if not relation or not re.search(r"[A-Za-z]", relation):
            rejected.append(f"Relation rejected (invalid relation type '{relation}'): {source} -> {target}")
            continue

        normalized_relation = normalize_relation_type(relation)
        if normalized_relation == RelationType.RELATED_TO.value and relation.upper() != RelationType.RELATED_TO.value:
            warnings.append(f"Relation type '{relation}' mapped to RELATED_TO ({source} -> {target})")

        if known_keys and surface_key(source) not in known_keys:
            warnings.append(f"Unresolved relation source '{source}' (may resolve across chunks)")

        accepted.append(
            RawRelation(
                source=source,
                relation=normalized_relation,
                target=target,
                confidence=data.get("confidence"),
                quote=str(data.get("quote") or ""),
            )
        )
    return accepted, warnings, rejected



# ---------------------------------------------------------------------------
# Raw -> canonical promotion (evidence is always attached here)
# ---------------------------------------------------------------------------
def to_doclink_entity(raw: RawEntity, evidence: Sequence[SourceSpan],
                      default_confidence: float = 0.85) -> DocLinkEntity:
    """Promote a validated raw entity to a canonical ``DocLinkEntity``."""
    return DocLinkEntity(
        entity_id="ent_000",
        text=raw.text,
        canonical_name=raw.canonical_name or raw.text,
        surface_forms=sorted({raw.text, raw.canonical_name or raw.text}),
        type=normalize_entity_type(raw.type) or raw.type,
        confidence=round(float(raw.confidence if raw.confidence is not None else default_confidence), 3),
        mentions=1,
        evidence=list(evidence),
        aliases_resolved=list(raw.aliases or []),
    )


def to_doclink_fact(raw: RawFact, evidence: Sequence[SourceSpan],
                    default_confidence: float = 0.85) -> DocLinkFact:
    """Promote a validated raw triple to a canonical ``DocLinkFact``."""
    fact_type = str(raw.fact_type or "").strip().upper()
    if fact_type not in FactType.__members__:
        fact_type = classify_fact_type(raw.statement or "")
    return DocLinkFact(
        fact_id="fact_000",
        statement=raw.statement or f"{raw.subject} {raw.predicate} {raw.object}".strip(),
        subject=raw.subject,
        predicate=raw.predicate,
        object=raw.object,
        time=raw.time,
        fact_type=fact_type,
        confidence=round(float(raw.confidence if raw.confidence is not None else default_confidence), 3),
        evidence=list(evidence),
    )


def to_doclink_relation(raw: RawRelation, evidence: Sequence[SourceSpan],
                        default_confidence: float = 0.85) -> DocLinkRelation:
    """Promote a validated raw relation to a canonical ``DocLinkRelation``."""
    return DocLinkRelation(
        relation_id="rel_000",
        source=raw.source,
        relation=normalize_relation_type(raw.relation),
        target=raw.target,
        confidence=round(float(raw.confidence if raw.confidence is not None else default_confidence), 3),
        evidence=list(evidence),
    )



# ---------------------------------------------------------------------------
# Result-level validation
# ---------------------------------------------------------------------------
def _duplicate_ids(items: Sequence[Any], attr: str) -> List[str]:
    seen: set = set()
    duplicates: List[str] = []
    for item in items:
        value = str(getattr(item, attr, "") or "")
        if not value:
            continue
        if value in seen:
            duplicates.append(f"{attr}={value}")
        seen.add(value)
    return duplicates


def validate_doclink_result(result: DocLinkResult) -> DocLinkValidationReport:
    """Audit a full ``DocLinkResult`` for structural + semantic integrity."""
    errors: List[str] = []
    warnings: List[str] = []
    checks: Dict[str, bool] = {}
    invalid_types: List[str] = []
    orphan_relations: List[str] = []
    missing_evidence: List[str] = []

    duplicate_ids = (
        _duplicate_ids(result.entities, "entity_id")
        + _duplicate_ids(result.facts, "fact_id")
        + _duplicate_ids(result.relations, "relation_id")
    )
    if duplicate_ids:
        errors.extend([f"Duplicate id: {d}" for d in duplicate_ids])
    checks["unique_ids"] = not duplicate_ids

    for entity in result.entities:
        if not is_valid_entity_type(entity.type):
            invalid_types.append(f"entity {entity.entity_id} type='{entity.type}'")
        if not entity.canonical_name.strip():
            invalid_types.append(f"entity {entity.entity_id} has empty canonical_name")
        if not entity.evidence:
            missing_evidence.append(entity.entity_id)
    checks["valid_entity_types"] = not invalid_types

    index = build_entity_index(result.entities)
    entity_ids = {e.entity_id for e in result.entities}

    for fact in result.facts:
        if not fact.subject.strip():
            errors.append(f"Fact {fact.fact_id} missing subject")
        if not fact.predicate.strip():
            errors.append(f"Fact {fact.fact_id} missing predicate")
        if not fact.evidence:
            missing_evidence.append(fact.fact_id)

    for relation in result.relations:
        if relation.relation.upper() not in RelationType.__members__:
            invalid_types.append(f"relation {relation.relation_id} type='{relation.relation}'")
        source_ok = (
            (relation.source_id in entity_ids if relation.source_id else False)
            or link_entity_reference(relation.source, index) is not None
        )
        target_ok = (
            (relation.target_id in entity_ids if relation.target_id else False)
            or link_entity_reference(relation.target, index) is not None
        )
        if not (source_ok or target_ok):
            orphan_relations.append(f"{relation.relation_id}: {relation.source} -> {relation.target}")
        if surface_key(relation.source) == surface_key(relation.target):
            errors.append(f"Relation {relation.relation_id} is a self-relation")
        if not relation.evidence:
            missing_evidence.append(relation.relation_id)

    if invalid_types:
        errors.extend([f"Invalid type: {t}" for t in invalid_types])
    if orphan_relations:
        warnings.extend([f"Relation with no resolvable endpoints: {o}" for o in orphan_relations])
    if missing_evidence:
        warnings.append(f"{len(missing_evidence)} item(s) without evidence spans")

    coverage = evidence_coverage(result.entities, result.facts, result.relations)
    checks["evidence_coverage"] = coverage >= 90.0
    checks["relationship_integrity"] = not orphan_relations
    checks["has_entities"] = len(result.entities) > 0
    checks["has_facts"] = len(result.facts) > 0
    checks["has_relations"] = len(result.relations) > 0
    checks["no_self_relations"] = not any("self-relation" in e for e in errors)

    stats = {
        "entities": len(result.entities),
        "facts": len(result.facts),
        "relations": len(result.relations),
        "chunks": len(result.chunks),
    }
    if result.statistics.totalEntities != stats["entities"]:
        warnings.append("Statistics mismatch: totalEntities")
    if result.statistics.totalFacts != stats["facts"]:
        warnings.append("Statistics mismatch: totalFacts")
    if result.statistics.totalRelations != stats["relations"]:
        warnings.append("Statistics mismatch: totalRelations")

    valid = len(errors) == 0
    return DocLinkValidationReport(
        valid=valid,
        status="valid" if valid else "invalid",
        documentId=result.document_id,
        stats=stats,
        errors=errors,
        warnings=warnings,
        orphanRelations=orphan_relations,
        duplicateIds=duplicate_ids,
        invalidTypes=invalid_types,
        missingEvidence=missing_evidence,
        evidenceCoverage=coverage,
        checks=checks,
    )


__all__ = [
    "MAX_ENTITY_TEXT_LENGTH",
    "MIN_ENTITY_TEXT_LENGTH",
    "MIN_FACT_STATEMENT_LENGTH",
    "classify_fact_type",
    "validate_raw_entities",
    "validate_raw_facts",
    "validate_raw_relations",
    "to_doclink_entity",
    "to_doclink_fact",
    "to_doclink_relation",
    "validate_doclink_result",
]

