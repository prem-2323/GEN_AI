"""Phase 13 Validation Engine — Entity Validator.

Validates extracted entities (PERSON, ORGANIZATION, LOCATION, PRODUCT, TECHNOLOGY, etc.)
against trusted source entities with canonical normalization.
"""

from __future__ import annotations

import re
import logging
from typing import List, Set
from .schemas import (
    IssueTypeEnum,
    SeverityEnum,
    ValidationContext,
    ValidationIssue,
)

log = logging.getLogger("gen-transform.validation.entity_validator")


class EntityValidator:
    """Validator auditing named entities against ground truth."""

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize canonical entity names to avoid false mismatch triggers."""
        name_clean = name.lower().strip()
        # Remove common business suffixes for org matching
        name_clean = re.sub(r"\b(inc|corp|corporation|ltd|llc|co)\b\.?", "", name_clean).strip()
        return name_clean

    def validate_entities(self, context: ValidationContext) -> List[ValidationIssue]:
        """Validate generated text entities against trusted source entities."""
        issues: List[ValidationIssue] = []
        gen_text = context.transformation_output or ""
        gen_text_lower = gen_text.lower()

        # Collect source entity canonical names
        source_entity_names: Set[str] = set()
        for ent in context.source_entities:
            raw_name = ent.get("name", "") if isinstance(ent, dict) else str(ent)
            if raw_name:
                source_entity_names.add(self._normalize_name(raw_name))

        # Also extract entities from evidence items if any
        for item in context.source_evidence:
            content = item.get("content", "") if isinstance(item, dict) else str(item)
            # Find capitalized entity-like tokens
            for match in re.findall(r"\b[A-Z][a-zA-Z0-9_-]+(?:\s+[A-Z][a-zA-Z0-9_-]+)*\b", content):
                source_entity_names.add(self._normalize_name(match))

        if not source_entity_names:
            return []

        # Check capitalized entity tokens in generated output against source entities
        gen_entities = re.findall(r"\b[A-Z][a-zA-Z0-9_-]+(?:\s+[A-Z][a-zA-Z0-9_-]+)*\b", gen_text)
        ignored_words = {
            "summary", "executive", "overview", "key", "findings", "conclusion",
            "title", "section", "deliverable", "factual", "detailed", "report",
            "evidence", "standard", "action", "items", "analysis", "content",
            "points", "details", "source", "facts"
        }

        for gen_ent in set(gen_entities):
            norm_gen = self._normalize_name(gen_ent)
            if len(norm_gen) <= 2 or norm_gen in ignored_words or any(w.lower() in ignored_words for w in gen_ent.split()):
                continue

            # If source entities exist, check if gen_ent matches any source entity
            if source_entity_names and norm_gen not in source_entity_names:
                # Check fuzzy or substring match
                if not any(norm_gen in s_ent or s_ent in norm_gen for s_ent in source_entity_names):
                    issues.append(
                        ValidationIssue(
                            issue_type=IssueTypeEnum.ENTITY_MISMATCH,
                            severity=SeverityEnum.ERROR,
                            message=f"Entity mismatch: Generated entity '{gen_ent}' not found in trusted source entities.",
                            generated_text=gen_ent,
                        )
                    )

        return issues


__all__ = ["EntityValidator"]
