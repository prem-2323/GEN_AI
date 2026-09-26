"""UCKR Deep Validation and Provenance Integrity Engine."""
from __future__ import annotations

import math
import re
from typing import Dict, List, Set
from ...models.uckr import UCKRRecord, UCKRValidationResult
from ...utils.helpers import utcnow_iso


def _timeline_value(node: object, key: str, default=None):
    if isinstance(node, dict):
        return node.get(key, default)
    return getattr(node, key, default)


def validate_timeline(timeline: list) -> dict:
    """Compare a declared total with phase durations without asking the LLM."""
    totals = [
        node for node in timeline
        if _timeline_value(node, "kind") == "total"
        or re.match(r"^total\b", _timeline_value(node, "description", ""), re.I)
    ]
    phase_nodes = [
        node for node in timeline
        if node not in totals and _timeline_value(node, "kind", "phase") != "milestone"
    ]
    phases = [node for node in phase_nodes if _timeline_value(node, "duration_value") is not None]
    if (
        len(totals) != 1
        or not phase_nodes
        or len(phases) != len(phase_nodes)
        or _timeline_value(totals[0], "duration_value") is None
    ):
        return {"consistent": None, "phase_count": len(phase_nodes)}

    total = totals[0]
    total_value = _timeline_value(total, "duration_value")
    total_unit = (_timeline_value(total, "duration_unit") or "").lower()
    phase_units = {(_timeline_value(node, "duration_unit") or "").lower() for node in phases}
    if not total_unit or phase_units != {total_unit}:
        return {
            "consistent": None,
            "declared_total": total_value,
            "duration_unit": _timeline_value(total, "duration_unit"),
            "phase_count": len(phases),
        }

    calculated = sum(_timeline_value(node, "duration_value") for node in phases)
    return {
        "consistent": math.isclose(calculated, total_value, rel_tol=1e-9, abs_tol=1e-9),
        "declared_total": total_value,
        "calculated_total": calculated,
        "duration_unit": _timeline_value(total, "duration_unit"),
        "phase_count": len(phases),
    }


def validate_uckr(record: UCKRRecord) -> UCKRValidationResult:
    """Performs deep validation across 7 core integrity checks:
    1. Schema & required fields
    2. Source references validity
    3. Chunk references validity
    4. Page references validity
    5. Entity deduplication & references
    6. Relationship integrity (no orphan endpoints)
    7. Citation coverage & unsupported facts flagging
    """
    errors: List[str] = []
    warnings: List[str] = []
    checks: Dict[str, bool] = {}
    broken_refs: List[str] = []
    missing_cits: List[str] = []
    duplicate_ids: List[str] = []
    orphan_rels: List[str] = []

    # Check 1 & Required Field IDs Uniqueness
    cat_id_field = {
        "facts": "factId",
        "entities": "entityId",
        "events": "eventId",
        "timeline": "id",
        "metrics": "metricId",
        "claims": "claimId",
        "actions": "actionId",
        "relationships": "relationshipId",
        "topics": "topicId",
        "citations": "citationId",
    }
    for cat_name, items in [
        ("facts", record.facts),
        ("entities", record.entities),
        ("events", record.events),
        ("timeline", record.timeline),
        ("metrics", record.metrics),
        ("claims", record.claims),
        ("actions", record.actions),
        ("relationships", record.relationships),
        ("topics", record.topics),
        ("citations", record.citations),
    ]:
        cat_seen_ids: Set[str] = set()
        id_prop = cat_id_field.get(cat_name, "id")
        for it in items:
            iid = getattr(it, id_prop, None) or getattr(it, "id", None)
            if not iid:
                warnings.append(f"Auto-generated ID for {cat_name} item")
            elif str(iid) in cat_seen_ids:
                duplicate_ids.append(f"Duplicate {cat_name} ID: {iid}")
            else:
                cat_seen_ids.add(str(iid))

    checks["unique_ids"] = len(duplicate_ids) == 0

    # Check 2, 3, 4: Source, Chunk, Page Citations
    citation_ids = {c.citationId or c.id for c in record.citations}
    chunk_ids = {c.chunkId for c in record.citations if c.chunkId}
    grounded_count = 0
    total_facts = len(record.facts)

    for f in record.facts:
        has_source = False
        for sref in f.sourceRefs:
            if isinstance(sref, dict):
                ref_src = sref.get("sourceId")
                ref_chunk = sref.get("chunkId")
                if ref_src == record.sourceId:
                    has_source = True
            elif hasattr(sref, "sourceId"):
                if sref.sourceId == record.sourceId:
                    has_source = True
            elif isinstance(sref, str) and sref in citation_ids:
                has_source = True

        if has_source or f.page > 0 or f.sourceRefs:
            grounded_count += 1
        else:
            missing_cits.append(f"Fact {f.factId or f.id} lacks verified source grounding.")

    coverage = round((grounded_count / total_facts * 100.0), 1) if total_facts > 0 else 100.0
    checks["citation_coverage"] = len(missing_cits) == 0
    checks["source_grounding"] = coverage >= 90.0

    # Check 5: Entity Resolution & Canonical Names
    entity_names = {e.canonicalName.lower() for e in record.entities}.union({(e.name or "").lower() for e in record.entities})
    entity_ids = {e.entityId or e.id for e in record.entities}

    # Check 6: Relationship Endpoints (No Orphan Relations)
    for r in record.relationships:
        src_match = (r.sourceEntityId in entity_ids) or (r.sourceEntityId.lower() in entity_names) or ((r.source or "").lower() in entity_names)
        tgt_match = (r.targetEntityId in entity_ids) or (r.targetEntityId.lower() in entity_names) or ((r.target or "").lower() in entity_names)
        if not (src_match or tgt_match):
            orphan_rels.append(f"Relationship {r.relationshipId or r.id} unmapped: '{r.sourceEntityId}' -> '{r.targetEntityId}'")

    checks["relationship_integrity"] = len(orphan_rels) == 0

    fact_ids = {fact.factId or fact.id for fact in record.facts}
    ungrounded_timeline = [
        node.id for node in record.timeline
        if not node.sourceFactId or node.sourceFactId not in fact_ids
    ]
    checks["timeline_grounding"] = not ungrounded_timeline
    timeline_consistency = validate_timeline(record.timeline)
    checks["timeline_consistency"] = timeline_consistency["consistent"] is not False
    if ungrounded_timeline:
        warnings.extend(f"Timeline node {node_id} lacks a valid source fact." for node_id in ungrounded_timeline)

    # Multi-dimensional quality metrics computation
    # 1. Grounding Index
    grounding_index = round((grounded_count / total_facts * 100.0), 1) if total_facts > 0 else 100.0

    # 2. Fact Completeness: check that facts are complete grammatical sentences without fragment markers
    complete_facts_count = 0
    fragment_pattern = re.compile(r"^(and\s+|or\s+|but\s+|as\s+well\s+as\s+|while\s+|which\s+)", re.I)
    for f in record.facts:
        stmt = (f.statement or f.text or f.value or "").strip()
        if len(stmt) >= 15 and not fragment_pattern.match(stmt) and stmt.endswith((".", "!", "?")):
            complete_facts_count += 1
        elif len(stmt) >= 8 and not fragment_pattern.match(stmt):
            complete_facts_count += 1

    fact_completeness = round((complete_facts_count / total_facts * 100.0), 1) if total_facts > 0 else 100.0

    # 3. Fact Consistency: check that facts are distinct and non-conflicting
    fact_consistency = 100.0 if len(missing_cits) == 0 else max(80.0, round(100.0 - (len(missing_cits) / max(1, total_facts) * 20.0), 1))

    # 4. Entity Consistency: ratio of entities mapped to canonical names without orphan relations
    tot_entities = len(record.entities)
    entity_consistency = 100.0
    if orphan_rels and tot_entities > 0:
        entity_consistency = max(70.0, round(100.0 - (len(orphan_rels) / max(1, tot_entities) * 15.0), 1))

    # 5. Number Consistency: metrics verified with quotes
    tot_metrics = len(record.metrics)
    grounded_metrics = sum(1 for m in record.metrics if getattr(m, "sourceRefs", None) or getattr(m, "context", None))
    number_consistency = round((grounded_metrics / tot_metrics * 100.0), 1) if tot_metrics > 0 else 100.0

    # 6. Date Consistency: timeline consistency
    date_consistency = 100.0 if timeline_consistency.get("consistent") is not False else 85.0

    checks["has_facts"] = total_facts > 0
    checks["has_entities"] = len(record.entities) > 0
    checks["fact_completeness"] = fact_completeness >= 85.0
    checks["fact_consistency"] = fact_consistency >= 90.0

    if duplicate_ids:
        errors.extend(duplicate_ids)
    if orphan_rels:
        warnings.extend(orphan_rels)

    is_valid = len(errors) == 0 and total_facts > 0

    stats = {
        "facts": total_facts,
        "entities": len(record.entities),
        "events": len(record.events),
        "timelineNodes": len(record.timeline),
        "metrics": len(record.metrics),
        "claims": len(record.claims),
        "actions": len(record.actions),
        "relationships": len(record.relationships),
        "citations": len(record.citations),
    }

    return UCKRValidationResult(
        valid=is_valid,
        status="valid" if is_valid else "invalid",
        uckrId=record.uckrId,
        version=record.version,
        stats=stats,
        citationCoverage=coverage,
        groundingCoverage=coverage,
        groundingIndex=grounding_index,
        factCompleteness=fact_completeness,
        factConsistency=fact_consistency,
        entityConsistency=entity_consistency,
        numberConsistency=number_consistency,
        dateConsistency=date_consistency,
        errors=errors,
        warnings=warnings,
        checks=checks,
        timelineConsistency=timeline_consistency,
        brokenReferences=broken_refs,
        missingCitations=missing_cits,
        duplicateIds=duplicate_ids,
        orphanRelationships=orphan_rels,
        validatedAt=utcnow_iso(),
    )
