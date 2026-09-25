"""Phase 13 Validation Engine — Citation Validator.

Audits inline citation references ([1], [2], etc.) in generated outputs against valid
citation contexts from Phase 7/8, detecting invalid or hallucinated citation IDs.
"""

from __future__ import annotations

import re
import logging
from typing import Dict, List, Set, Tuple
from .schemas import (
    IssueTypeEnum,
    SeverityEnum,
    ValidationContext,
    ValidationIssue,
)

log = logging.getLogger("gen-transform.validation.citation_validator")


class CitationValidator:
    """Validator auditing citation tags and mapping integrity."""

    def validate_citations(
        self, context: ValidationContext
    ) -> Tuple[List[ValidationIssue], Dict[str, str]]:
        """Audit citation tags in generated text against valid context citations.

        Returns:
            Tuple of (issues_list, citation_validity_map)
        """
        issues: List[ValidationIssue] = []
        gen_text = context.transformation_output or ""

        # Collect valid citation IDs from context
        valid_citations: Dict[str, str] = {}
        for cit in context.citations:
            if isinstance(cit, dict):
                c_id = cit.get("citation_id", "")
                e_id = cit.get("evidence_id", "")
            else:
                c_id = getattr(cit, "citation_id", "")
                e_id = getattr(cit, "evidence_id", "")

            if c_id is not None and c_id != "":
                c_id_str = str(c_id).strip()
                valid_citations[c_id_str] = str(e_id)
                if not c_id_str.startswith("["):
                    valid_citations[f"[{c_id_str}]"] = str(e_id)
                else:
                    valid_citations[c_id_str.strip("[]")] = str(e_id)

        # Extract all citation tags in generated text
        found_tags = set(re.findall(r"\[\d+\]", gen_text))

        for tag in found_tags:
            if valid_citations and tag not in valid_citations:
                msg = f"Citation invalid: Nonexistent or hallucinated citation ID {tag} detected in generated deliverable."
                issues.append(
                    ValidationIssue(
                        issue_type=IssueTypeEnum.CITATION_INVALID,
                        severity=SeverityEnum.CRITICAL,
                        message=msg,
                        generated_text=tag,
                    )
                )

        if not found_tags and valid_citations:
            issues.append(
                ValidationIssue(
                    issue_type=IssueTypeEnum.CITATION_MISSING,
                    severity=SeverityEnum.WARNING,
                    message="Source evidence contains citations, but no inline citations were included in generated output.",
                )
            )

        return issues, valid_citations


__all__ = ["CitationValidator"]
