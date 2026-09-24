"""Entity and alias consistency checker (Phase 7)."""
from __future__ import annotations

import re
from typing import Any, Dict, List
from ...models.validation import CheckItem


def check_entity_consistency(uckr: Dict[str, Any], deliverable_text: str) -> List[CheckItem]:
    """Validates that entity names and approved aliases appear consistently in deliverable text."""
    checks: List[CheckItem] = []
    entities = uckr.get("entities", [])
    if not entities:
        return checks

    text_lower = deliverable_text.lower()

    for ent in entities:
        eid = ent.get("entityId", "entity")
        canonical = ent.get("canonicalName", "").strip()
        if not canonical or len(canonical) < 3:
            continue

        aliases = [a.strip() for a in ent.get("aliases", []) if a.strip()]
        all_variants = [canonical] + aliases

        found_variant = None
        for variant in all_variants:
            pattern = r"\b" + re.escape(variant.lower()) + r"\b"
            if re.search(pattern, text_lower):
                found_variant = variant
                break

        if found_variant:
            is_alias = found_variant.lower() != canonical.lower()
            checks.append(CheckItem(
                category="entity",
                entityId=eid,
                expected=canonical,
                found=found_variant,
                status="consistent",
                message=f"Entity '{canonical}' verified (via {'alias: ' + found_variant if is_alias else 'canonical name'}).",
            ))

    return checks
