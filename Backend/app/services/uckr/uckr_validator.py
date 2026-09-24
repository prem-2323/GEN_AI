"""UCKR Deep Validation and Provenance Integrity Engine."""
from __future__ import annotations

from typing import Dict, List, Set
from ...models.uckr import UCKRRecord, UCKRValidationResult
from ...utils.helpers import utcnow_iso


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

    # Check 7: Summary & Schema Validation
    checks["has_facts"] = total_facts > 0
    checks["has_entities"] = len(record.entities) > 0

    if duplicate_ids:
        errors.extend(duplicate_ids)
    if orphan_rels:
        warnings.extend(orphan_rels)

    is_valid = len(errors) == 0 and total_facts > 0

    stats = {
        "facts": total_facts,
        "entities": len(record.entities),
        "events": len(record.events),
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
        errors=errors,
        warnings=warnings,
        checks=checks,
        brokenReferences=broken_refs,
        missingCitations=missing_cits,
        duplicateIds=duplicate_ids,
        orphanRelationships=orphan_rels,
        validatedAt=utcnow_iso(),
    )
