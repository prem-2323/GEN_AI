"""Output Validator for Transformation Engine Deliverables.

Validates:
1. Target schema compliance using Pydantic models.
2. Fact ID grounding — every referenced fact must exist in the source UCKR.
3. Citation / provenance integrity.
4. Rejects hallucinated fact IDs (e.g. 'fact_999').
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Set, Tuple
from ...models.deliverable import DeliverableType
from .schemas import DELIVERABLE_MODEL_MAP

log = logging.getLogger("gen-transform.output_validator")


def extract_used_fact_ids_from_content(content: Dict[str, Any]) -> List[str]:
    """Recursively collects all fact IDs declared anywhere in the content dict."""
    used_ids: Set[str] = set()

    # Top-level usedFactIds
    if "usedFactIds" in content and isinstance(content["usedFactIds"], list):
        for fid in content["usedFactIds"]:
            if isinstance(fid, str) and fid.strip():
                used_ids.add(fid.strip())

    # Nested in X posts
    for post in content.get("posts", []):
        if isinstance(post, dict):
            for fid in post.get("usedFactIds", []):
                if isinstance(fid, str) and fid.strip():
                    used_ids.add(fid.strip())

    # Nested in presentation slides
    for slide in content.get("slides", []):
        if isinstance(slide, dict):
            for fid in slide.get("usedFactIds", []):
                if isinstance(fid, str) and fid.strip():
                    used_ids.add(fid.strip())

    # Nested in video scenes
    for scene in content.get("scenes", []):
        if isinstance(scene, dict):
            for fid in scene.get("usedFactIds", []):
                if isinstance(fid, str) and fid.strip():
                    used_ids.add(fid.strip())

    return sorted(list(used_ids))


def validate_deliverable_output(
    dtype: DeliverableType,
    content: Dict[str, Any],
    uckr: Dict[str, Any],
) -> Tuple[bool, List[str], List[str], List[str]]:
    """Validates deliverable content structure and UCKR fact grounding.

    Returns:
        (is_valid, errors, warnings, validated_fact_ids)
    """
    errors: List[str] = []
    warnings: List[str] = []

    # 1. Pydantic Schema Validation
    model_cls = DELIVERABLE_MODEL_MAP.get(dtype)
    if model_cls:
        try:
            model_cls.model_validate(content)
        except Exception as exc:
            errors.append(f"Schema validation failed for {dtype}: {str(exc)[:200]}")

    # 2. Fact Grounding Verification
    valid_uckr_fact_ids = {
        f.get("factId") for f in uckr.get("facts", []) if f.get("factId")
    }

    used_fact_ids = extract_used_fact_ids_from_content(content)
    unknown_fact_ids = [fid for fid in used_fact_ids if fid not in valid_uckr_fact_ids]

    if unknown_fact_ids:
        for ufid in unknown_fact_ids:
            errors.append(f"Unknown fact ID referenced: '{ufid}' does not exist in UCKR.")

    if not used_fact_ids and uckr.get("facts"):
        warnings.append("Deliverable does not explicitly tag any usedFactIds.")

    is_valid = len(errors) == 0
    return is_valid, errors, warnings, used_fact_ids
