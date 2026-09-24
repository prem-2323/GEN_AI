"""Relationship and knowledge graph mapping for UCKR Engine."""
from __future__ import annotations

from typing import Any, List, Set
from ...models.uckr import Relationship, SourceRef

_RELATION_TYPES = {
    "conduct": "CONDUCTED",
    "target": "TARGETED",
    "exploit": "TARGETED",
    "locate": "LOCATED_IN",
    "own": "OWNED_BY",
    "use": "USED",
    "produce": "PRODUCED",
    "affect": "AFFECTED",
    "impact": "AFFECTED",
    "cause": "CAUSED",
    "part": "PART_OF",
    "announce": "ANNOUNCED",
    "operate": "OPERATED_BY",
    "configure": "OPERATED_BY",
}


def _standardize_rel_type(raw_rel: str) -> str:
    r_lower = raw_rel.lower()
    for k, v in _RELATION_TYPES.items():
        if k in r_lower:
            return v
    return "RELATED_TO"


def process_relationships(
    raw_relationships: List[Any],
    source_id: str,
    valid_entity_names: Set[str],
    page_number: int = 1,
) -> List[Relationship]:
    """Validates and maps semantic relationships between entities."""
    relationships: List[Relationship] = []

    for idx, item in enumerate(raw_relationships, start=1):
        if isinstance(item, dict):
            src = (item.get("sourceEntityId") or item.get("source") or "").strip()
            rel = (item.get("relationshipType") or item.get("relation") or "RELATED_TO").strip()
            tgt = (item.get("targetEntityId") or item.get("target") or "").strip()
            conf = float(item.get("confidence", 0.92))
        else:
            continue

        if not src or not tgt:
            continue

        std_rel = _standardize_rel_type(rel)
        rid = f"rel_{len(relationships) + 1:03d}"

        sref = SourceRef(
            sourceId=source_id,
            chunkId=f"chunk_{page_number:03d}",
            pageNumber=page_number,
        )

        r = Relationship(
            relationshipId=rid,
            id=rid,
            sourceEntityId=src,
            source=src,
            relationshipType=std_rel,
            relation=std_rel,
            targetEntityId=tgt,
            target=tgt,
            confidence=round(conf, 3),
            sourceRefs=[sref],
        )
        relationships.append(r)

    return relationships
