"""Phase 5 UCKR Engine exports."""
from .uckr_builder import (
    build_and_save_uckr,
    build_uckr_from_analysis,
    get_latest_uckr_record,
    get_uckr_validation_report,
    get_uckr_version,
    list_uckr_versions,
    save_uckr_record,
)
from .uckr_validator import validate_uckr
from .entity_resolver import resolve_and_deduplicate_entities
from .fact_service import classify_fact_type, process_and_deduplicate_facts
from .uckr_normalizer import (
    normalize_events,
    normalize_metrics,
    normalize_claims,
    normalize_actions,
)
from .relationship_service import process_relationships
from .citation_service import build_citations

__all__ = [
    "build_and_save_uckr",
    "build_uckr_from_analysis",
    "get_latest_uckr_record",
    "get_uckr_validation_report",
    "get_uckr_version",
    "list_uckr_versions",
    "save_uckr_record",
    "validate_uckr",
    "resolve_and_deduplicate_entities",
    "classify_fact_type",
    "process_and_deduplicate_facts",
    "normalize_events",
    "normalize_metrics",
    "normalize_claims",
    "normalize_actions",
    "process_relationships",
    "build_citations",
]
