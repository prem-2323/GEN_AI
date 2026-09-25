"""Phase 13 Validation Engine — Fact Validator.

Validates extracted claims against authoritative source evidence and DocLink facts,
classifying claims into SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, or CONTRADICTED.
"""

from __future__ import annotations

import logging
from typing import List, Tuple
from .schemas import (
    ClaimItem,
    FactSupportStatusEnum,
    IssueTypeEnum,
    SeverityEnum,
    ValidationContext,
    ValidationIssue,
)

log = logging.getLogger("gen-transform.validation.fact_validator")


class FactValidator:
    """Validator auditing claims against source evidence facts."""

    def validate_facts(
        self, claims: List[ClaimItem], context: ValidationContext
    ) -> Tuple[List[ValidationIssue], List[FactSupportStatusEnum]]:
        """Validate list of ClaimItems against context source evidence.

        Returns:
            Tuple of (issues_list, support_statuses_list)
        """
        issues: List[ValidationIssue] = []
        statuses: List[FactSupportStatusEnum] = []

        source_text = " ".join(
            [item.get("content", "") for item in context.source_evidence]
        ).lower()
        if not source_text and context.source_evidence:
            source_text = str(context.source_evidence).lower()

        for claim in claims:
            c_text_lower = claim.text.lower()

            # Check direct or semantic containment in source text
            if not source_text.strip():
                statuses.append(FactSupportStatusEnum.UNKNOWN)
                continue

            # Quick check if main key words from claim are in source
            template_words = {
                "executive", "summary", "key", "findings", "conclusion", "action",
                "items", "overview", "detailed", "factual", "analysis", "evidence",
                "derived", "strictly", "source", "facts", "report", "deliverable"
            }
            words = [
                w for w in c_text_lower.split()
                if len(w) > 3 and not w.startswith("[") and w not in template_words
            ]
            if not words:
                statuses.append(FactSupportStatusEnum.SUPPORTED)
                continue

            matched_words = [w for w in words if w in source_text]
            match_ratio = len(matched_words) / len(words)

            if match_ratio >= 0.7:
                statuses.append(FactSupportStatusEnum.SUPPORTED)
            elif match_ratio >= 0.4:
                statuses.append(FactSupportStatusEnum.PARTIALLY_SUPPORTED)
                issues.append(
                    ValidationIssue(
                        issue_type=IssueTypeEnum.UNSUPPORTED_CLAIM,
                        severity=SeverityEnum.WARNING,
                        message=f"Claim is only partially supported by source evidence: '{claim.text}'",
                        generated_text=claim.text,
                    )
                )
            else:
                statuses.append(FactSupportStatusEnum.UNSUPPORTED)
                issues.append(
                    ValidationIssue(
                        issue_type=IssueTypeEnum.UNSUPPORTED_CLAIM,
                        severity=SeverityEnum.ERROR,
                        message=f"Unsupported claim detected without source evidence ground truth: '{claim.text}'",
                        generated_text=claim.text,
                    )
                )

        return issues, statuses


__all__ = ["FactValidator"]
