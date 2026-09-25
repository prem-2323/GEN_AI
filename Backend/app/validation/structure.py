"""Phase 13 Validation Engine — Structural Validator.

Verifies generated outputs against required section structures, output profile schemas,
and field completeness requirements.
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

log = logging.getLogger("gen-transform.validation.structure")


class StructuralValidator:
    """Validator checking document section structure and required field presence."""

    def validate_structure(
        self, context: ValidationContext
    ) -> List[ValidationIssue]:
        """Validate structure and required sections against context expected_structure."""
        issues: List[ValidationIssue] = []
        gen_text = context.transformation_output or ""
        expected_sections: List[str] = context.expected_structure or []

        if not expected_sections:
            return issues

        # Extract markdown headers from generated text
        headers = re.findall(r"^#{1,3}\s+(.+)$", gen_text, re.MULTILINE)
        header_names_lower: Set[str] = {
            h.strip().lower().replace(" ", "_") for h in headers
        }

        for sec in expected_sections:
            sec_lower = sec.lower().replace(" ", "_")
            sec_clean = sec.replace("_", " ")

            # Check if required section header or key phrase exists
            found = False
            if sec_lower in header_names_lower:
                found = True
            else:
                for h in header_names_lower:
                    if sec_lower in h or h in sec_lower:
                        found = True
                        break

            if not found:
                msg = f"Structural violation: Required section '{sec_clean}' is missing from generated deliverable."
                issues.append(
                    ValidationIssue(
                        issue_type=IssueTypeEnum.REQUIRED_FIELD_MISSING,
                        severity=SeverityEnum.WARNING,
                        message=msg,
                        location=sec,
                    )
                )

        return issues


__all__ = ["StructuralValidator"]
