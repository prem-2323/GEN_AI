"""Phase 13 Validation Engine — Metrics & Performance Measurement.

Tracks latency breakdown (claim extraction, fact validation, citation validation,
consistency evaluation) and calculates validation metrics.
"""

from __future__ import annotations

from typing import Dict, List
from .schemas import ValidationIssue, SeverityEnum


class ValidationMetricsCalculator:
    """Calculator for validation scores, issue counts, and check breakdowns."""

    @staticmethod
    def calculate_score(issues: List[ValidationIssue]) -> float:
        """Calculate score in range [0.0, 1.0] based on issue severity weights."""
        if not issues:
            return 1.0

        penalty = 0.0
        for issue in issues:
            sev = issue.severity.upper() if isinstance(issue.severity, str) else issue.severity
            if sev == "CRITICAL":
                penalty += 0.4
            elif sev == "ERROR":
                penalty += 0.2
            elif sev == "WARNING":
                penalty += 0.05
            elif sev == "INFO":
                penalty += 0.01

        score = max(0.0, round(1.0 - penalty, 4))
        return score

    @staticmethod
    def categorize_issues(
        issues: List[ValidationIssue]
    ) -> Dict[str, List[ValidationIssue]]:
        """Group issues into warnings, errors, and critical lists."""
        warnings: List[ValidationIssue] = []
        errors: List[ValidationIssue] = []

        for issue in issues:
            sev = issue.severity.upper() if isinstance(issue.severity, str) else issue.severity
            if sev in ("ERROR", "CRITICAL"):
                errors.append(issue)
            else:
                warnings.append(issue)

        return {"warnings": warnings, "errors": errors}


__all__ = ["ValidationMetricsCalculator"]
