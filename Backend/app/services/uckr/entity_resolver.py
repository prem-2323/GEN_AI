"""Entity resolution and alias normalization engine for UCKR."""
from __future__ import annotations

import re
from typing import Any, Dict, List
from ...models.uckr import Entity, SourceRef

_TYPE_MAP = {
    "organization": "ORGANIZATION",
    "person": "PERSON",
    "location": "LOCATION",
    "technology": "TECHNOLOGY",
    "threat_actor": "THREAT_ACTOR",
    "product": "PRODUCT",
    "malware": "MALWARE",
    "country": "COUNTRY",
    "system": "SYSTEM",
    "vulnerability": "TECHNOLOGY",
    "actor": "ORGANIZATION",
}


def _clean_cluster_key(name: str) -> str:
    """Strip corporate suffixes and non-alphanumeric chars to cluster name variants."""
    clean = name.strip().lower()
    clean = re.sub(r"\b(corporation|corp|incorporated|inc|ltd|limited|co|llc|group|technologies|solutions)\b\.?", "", clean)
    clean = re.sub(r"[^\w\s]", "", clean)
    return " ".join(clean.split())


def resolve_and_deduplicate_entities(
    raw_entities: List[Any],
    source_id: str,
    page_number: int = 1,
) -> List[Entity]:
    """Clusters entity variations, identifies canonical names, and maps aliases."""
    clusters: Dict[str, Dict[str, Any]] = {}

    for item in raw_entities:
        if isinstance(item, dict):
            name = (item.get("name") or item.get("canonicalName") or "").strip()
            raw_type = (item.get("type") or "ORGANIZATION").lower()
            role = (item.get("role") or "").strip()
            conf = float(item.get("confidence", 0.99))
            mentions = int(item.get("mentions", 1))
            aliases = list(item.get("aliases", []))
            srefs = item.get("sourceRefs", [])
        else:
            name = str(item).strip()
            raw_type = "organization"
            role = ""
            conf = 0.95
            mentions = 1
            aliases = []
            srefs = []

        if not name or len(name) < 2:
            continue

        std_type = _TYPE_MAP.get(raw_type, "ORGANIZATION")
        if any(t in name.lower() for t in ["cve-", "oauth", "saml", "ebpf", "tls", "api", "gateway", "proxy", "token"]):
            std_type = "TECHNOLOGY"
        elif any(t in name.lower() for t in ["storm", "apt", "phantom", "spider", "bear", "panda", "lazarus"]):
            std_type = "THREAT_ACTOR"

        key = _clean_cluster_key(name) or name.lower()

        if key not in clusters:
            clusters[key] = {
                "canonicalName": name,
                "names": {name},
                "type": std_type,
                "role": role,
                "confidence": conf,
                "mentions": mentions,
                "aliases": set(aliases),
                "sourceRefs": srefs,
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
        eid = f"entity_{idx:03d}"
        all_aliases = sorted(list(val["names"].union(val["aliases"]) - {val["canonicalName"]}))

        t = val["type"]
        if t in ("PERSON", "ORGANIZATION", "THREAT_ACTOR"):
            cat = "Actor / Stakeholder"
        elif t in ("TECHNOLOGY", "PRODUCT", "SYSTEM"):
            cat = "Technology / Standard"
        elif t in ("LOCATION", "COUNTRY"):
            cat = "Specification"
        else:
            cat = "Infrastructure / Asset"

        sref = SourceRef(
            sourceId=source_id,
            chunkId=f"chunk_{page_number:03d}",
            pageNumber=page_number,
        )

        ent = Entity(
            entityId=eid,
            id=eid,
            canonicalName=val["canonicalName"],
            name=val["canonicalName"],
            type=val["type"],
            category=cat,
            aliases=all_aliases,
            mentions=val["mentions"],
            role=val["role"],
            confidence=round(val["confidence"], 3),
            sourceRefs=[sref],
        )
        entities.append(ent)

    return entities
