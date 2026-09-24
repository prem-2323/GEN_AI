"""Entity resolution, alias grouping, and normalization for UCKR Engine."""
from __future__ import annotations

import re
from typing import Any, Dict, List
from ...models.uckr import Entity


def _canonical_entity_key(name: str) -> str:
    """Generate a cluster key to merge name variations (Inc, Corp, Ltd, etc)."""
    clean = name.strip().lower()
    clean = re.sub(r"\b(corporation|corp|incorporated|inc|ltd|limited|co|llc|group)\b\.?", "", clean)
    clean = re.sub(r"[^\w\s]", "", clean)
    return " ".join(clean.split())


def process_and_resolve_entities(
    raw_entities: List[Any],
    doc_name: str = "source",
) -> List[Entity]:
    """Clusters name variations, aggregates aliases & mentions, and outputs normalized Entities."""
    clusters: Dict[str, Dict[str, Any]] = {}

    for item in raw_entities:
        if isinstance(item, dict):
            name = (item.get("name") or "").strip()
            etype = (item.get("type") or "organization").lower()
            role = (item.get("role") or "").strip()
            conf = float(item.get("confidence", 0.98))
            mentions = int(item.get("mentions", 1))
            aliases = list(item.get("aliases", []))
        else:
            name = str(item).strip()
            etype = "organization"
            role = ""
            conf = 0.95
            mentions = 1
            aliases = []

        if not name or len(name) < 2:
            continue

        key = _canonical_entity_key(name)
        if not key:
            key = name.lower()

        if key not in clusters:
            clusters[key] = {
                "canonicalName": name,
                "names": {name},
                "type": etype,
                "role": role,
                "confidence": conf,
                "mentions": mentions,
                "aliases": set(aliases),
            }
        else:
            c = clusters[key]
            c["names"].add(name)
            c["mentions"] += mentions
            c["confidence"] = max(c["confidence"], conf)
            if len(name) > len(c["canonicalName"]):
                c["canonicalName"] = name
            if not c["role"] and role:
                c["role"] = role
            c["aliases"].update(aliases)

    entities: List[Entity] = []
    for idx, (key, val) in enumerate(clusters.items(), start=1):
        eid = f"ENT_{idx:03d}"
        all_aliases = sorted(list(val["names"].union(val["aliases"]) - {val["canonicalName"]}))
        
        # Categorize for UI
        t = val["type"]
        if t in ("person", "threat_actor", "organization", "actor"):
            cat = "Actor / Stakeholder"
        elif t in ("technology", "product", "system", "infrastructure", "vulnerability"):
            cat = "Technology & Infrastructure"
        elif t in ("location", "country"):
            cat = "Geography & Scope"
        else:
            cat = "Concept / Target"

        ent = Entity(
            id=eid,
            entityId=eid,
            name=val["canonicalName"],
            canonicalName=val["canonicalName"],
            type=val["type"],
            category=cat,
            aliases=all_aliases,
            mentions=val["mentions"],
            role=val["role"],
            confidence=round(val["confidence"], 3),
            sourceRefs=[f"CIT_ENT_{idx:03d}"],
        )
        entities.append(ent)

    return entities
