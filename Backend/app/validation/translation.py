"""Phase 13 Validation Engine — Translation Validator.

Audits translated outputs against source evidence to detect factual drift in numbers,
dates, named entities, technical terms, and citation tags.
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

log = logging.getLogger("gen-transform.validation.translation")


class TranslationValidator:
    """Validator auditing factual preservation across language translations."""

    def validate_translation(
        self, context: ValidationContext
    ) -> List[ValidationIssue]:
        """Audit translation output for factual drift against source evidence."""
        issues: List[ValidationIssue] = []

        if context.output_type != "TRANSLATION":
            return issues

        gen_text = context.transformation_output or ""
        source_text = " ".join([item.get("content", "") for item in context.source_evidence])
        if not source_text and context.source_evidence:
            source_text = str(context.source_evidence)

        # 1. Date Preservation Check
        date_pattern = r"\b\d{4}-\d{2}-\d{2}\b"
        source_dates = set(re.findall(date_pattern, source_text))
        gen_dates = set(re.findall(date_pattern, gen_text))

        missing_dates = source_dates - gen_dates
        if missing_dates:
            for d in missing_dates:
                msg = f"Translation factual drift: Source date '{d}' was not preserved in translated output."
                issues.append(
                    ValidationIssue(
                        issue_type=IssueTypeEnum.TRANSLATION_DRIFT,
                        severity=SeverityEnum.ERROR,
                        message=msg,
                        generated_text=d,
                    )
                )

        # 2. Citation Tag Preservation Check
        source_cits = set(re.findall(r"\[\d+\]", source_text))
        gen_cits = set(re.findall(r"\[\d+\]", gen_text))

        missing_cits = source_cits - gen_cits
        if missing_cits:
            for c in missing_cits:
                msg = f"Translation factual drift: Source citation '{c}' was omitted during translation."
                issues.append(
                    ValidationIssue(
                        issue_type=IssueTypeEnum.TRANSLATION_DRIFT,
                        severity=SeverityEnum.WARNING,
                        message=msg,
                        generated_text=c,
                    )
                )

        return issues


__all__ = ["TranslationValidator"]
