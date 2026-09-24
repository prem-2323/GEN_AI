"""Consistency Engine Package (Phase 7)."""
from .consistency_service import (
    validate_project_sources,
    validate_single_deliverable,
    get_latest_validation,
    regenerate_deliverable_with_feedback,
)
from .date_checker import check_date_consistency, normalize_date_to_iso
from .metric_checker import check_metric_consistency
from .entity_checker import check_entity_consistency
from .fact_checker import check_fact_preservation
from .citation_checker import check_citation_consistency
from .unsupported_claim_detector import detect_unsupported_claims
from .score_calculator import calculate_validation_scores

__all__ = [
    "validate_project_sources",
    "validate_single_deliverable",
    "get_latest_validation",
    "regenerate_deliverable_with_feedback",
    "check_date_consistency",
    "normalize_date_to_iso",
    "check_metric_consistency",
    "check_entity_consistency",
    "check_fact_preservation",
    "check_citation_consistency",
    "detect_unsupported_claims",
    "calculate_validation_scores",
]
