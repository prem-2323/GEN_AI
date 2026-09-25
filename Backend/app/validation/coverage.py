"""Phase 13 Validation Engine — Evidence Coverage Analyzer.

Measures the proportion of generated factual claims supported by authoritative evidence.
"""

from __future__ import annotations

import logging
from typing import List
from .schemas import EvidenceCoverageResult, FactSupportStatusEnum

log = logging.getLogger("gen-transform.validation.coverage")


class EvidenceCoverageAnalyzer:
    """Analyzer calculating evidence coverage ratio across extracted claims."""

    def analyze_coverage(
        self, statuses: List[FactSupportStatusEnum]
    ) -> EvidenceCoverageResult:
        """Calculate EvidenceCoverageResult from list of FactSupportStatusEnum items."""
        total = len(statuses)
        if total == 0:
            return EvidenceCoverageResult(
                total_claims=0,
                supported_claims=0,
                partially_supported_claims=0,
                unsupported_claims=0,
                contradicted_claims=0,
                coverage_ratio=1.0,
            )

        sup = statuses.count(FactSupportStatusEnum.SUPPORTED)
        part = statuses.count(FactSupportStatusEnum.PARTIALLY_SUPPORTED)
        unsup = statuses.count(FactSupportStatusEnum.UNSUPPORTED)
        contra = statuses.count(FactSupportStatusEnum.CONTRADICTED)

        weighted_support = sup + (0.5 * part)
        ratio = round(weighted_support / float(total), 4)

        return EvidenceCoverageResult(
            total_claims=total,
            supported_claims=sup,
            partially_supported_claims=part,
            unsupported_claims=unsup,
            contradicted_claims=contra,
            coverage_ratio=ratio,
        )


__all__ = ["EvidenceCoverageAnalyzer"]
