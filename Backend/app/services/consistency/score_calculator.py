"""Dynamic Score and Status Calculator for Phase 7 Consistency Engine."""
from __future__ import annotations

from typing import List, Tuple
from ...models.validation import (
    CheckItem,
    DeliverableValidationResult,
    OverallValidationStatus,
    ValidationScores,
)


def calculate_validation_scores(results: List[DeliverableValidationResult]) -> Tuple[ValidationScores, OverallValidationStatus]:
    """Dynamically calculates mathematical validation scores without any hardcoding."""
    all_checks: List[CheckItem] = []
    total_unsupported = 0

    for res in results:
        all_checks.extend(res.checks)
        total_unsupported += len(res.unsupportedClaims)

    if not all_checks:
        return (
            ValidationScores(
                consistency=100.0,
                factPreservation=100.0,
                citationCoverage=100.0,
                unsupportedClaims=total_unsupported,
            ),
            "PASS" if total_unsupported == 0 else "WARNING",
        )

    # 1. Consistency Score
    consistent_checks = sum(1 for c in all_checks if c.status == "consistent")
    contradictions = sum(1 for c in all_checks if c.status == "contradiction")
    total_checks = len(all_checks)
    consistency_pct = round((consistent_checks / max(1, total_checks)) * 100, 1)

    # 2. Fact Preservation Score
    fact_checks = [c for c in all_checks if c.category == "fact"]
    preserved_facts = sum(1 for c in fact_checks if c.status == "consistent")
    fact_pres_pct = round((preserved_facts / max(1, len(fact_checks))) * 100, 1) if fact_checks else 100.0

    # 3. Citation Coverage
    cit_checks = [c for c in all_checks if c.category == "citation"]
    valid_cits = sum(1 for c in cit_checks if c.status == "consistent")
    cit_coverage_pct = round((valid_cits / max(1, len(cit_checks))) * 100, 1) if cit_checks else 100.0

    scores = ValidationScores(
        consistency=consistency_pct,
        factPreservation=fact_pres_pct,
        citationCoverage=cit_coverage_pct,
        unsupportedClaims=total_unsupported,
    )

    # 4. Overall Status Determination
    if contradictions > 0 or consistency_pct < 70.0:
        overall_status: OverallValidationStatus = "FAIL"
    elif total_unsupported > 0 or consistency_pct < 90.0 or cit_coverage_pct < 80.0:
        overall_status = "WARNING"
    else:
        overall_status = "PASS"

    return scores, overall_status
