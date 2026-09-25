"""Phase 13 Validation Engine — Contradiction Detector.

Detects explicit evidence-grounded contradictions between generated content
and authoritative source ground truth.
"""

from __future__ import annotations

import re
import logging
from typing import List
from .schemas import (
    IssueTypeEnum,
    SeverityEnum,
    ValidationContext,
    ValidationIssue,
)

log = logging.getLogger("gen-transform.validation.contradiction")


class ContradictionDetector:
    """Detector auditing output for explicit factual contradictions."""

    def detect_contradictions(
        self, context: ValidationContext
    ) -> List[ValidationIssue]:
        """Detect explicit factual contradictions against trusted source content."""
        issues: List[ValidationIssue] = []
        gen_text = context.transformation_output or ""
        gen_lower = gen_text.lower()

        source_content = " ".join([item.get("content", "") for item in context.source_evidence])
        if not source_content and context.source_evidence:
            source_content = str(context.source_evidence)
        source_lower = source_content.lower()

        if not source_lower.strip():
            return issues

        # 1. Date Contradictions (e.g., source says 2026-01-10, output says 2026-01-12 or 2026-01-15)
        date_pattern = r"\b\d{4}-\d{2}-\d{2}\b"
        gen_dates = set(re.findall(date_pattern, gen_text))
        source_dates = set(re.findall(date_pattern, source_content))

        if source_dates and gen_dates:
            contradictory_dates = gen_dates - source_dates
            for c_date in contradictory_dates:
                msg = f"Contradiction detected: Output claims date '{c_date}' which directly contradicts trusted source date(s) {sorted(source_dates)}."
                issues.append(
                    ValidationIssue(
                        issue_type=IssueTypeEnum.CONTRADICTION,
                        severity=SeverityEnum.CRITICAL,
                        message=msg,
                        generated_text=c_date,
                    )
                )

        # 2. Negation Contradictions (e.g., source says "uses Technology C", output says "does not use Technology C")
        negation_terms = ["does not", "is not", "not", "never", "no", "without", "unable", "refused", "cancelled", "denied"]
        for fact in context.source_facts:
            subj = fact.get("subject", "").lower()
            pred = fact.get("predicate", "").lower()
            obj = fact.get("object_val", fact.get("object", "")).lower()

            if obj and obj in gen_lower:
                for neg in negation_terms:
                    if (f"{neg} {pred}" in gen_lower or f"{neg} {obj}" in gen_lower or f"does not {pred}" in gen_lower or f"does not use {obj}" in gen_lower):
                        if neg not in source_lower:
                            msg = f"Contradiction detected: Output negates factual relation involving '{obj}'."
                            issues.append(
                                ValidationIssue(
                                    issue_type=IssueTypeEnum.CONTRADICTION,
                                    severity=SeverityEnum.CRITICAL,
                                    message=msg,
                                    generated_text=f"{neg} {obj}",
                                )
                            )
                            break

        return issues


__all__ = ["ContradictionDetector"]
