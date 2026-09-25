"""Phase 13 Validation & Consistency Engine Module.

Provides automated validation of generated deliverables against authoritative ground truth evidence,
detecting unsupported claims, changed facts, dates, numbers, names, citations, contradictions,
and cross-output discrepancies.
"""

from .citation_validator import CitationValidator
from .claim_validator import ClaimExtractor
from .config import ValidationSettings, get_validation_settings
from .consistency import CrossOutputConsistencyEngine
from .contradiction import ContradictionDetector
from .coverage import EvidenceCoverageAnalyzer
from .entity_validator import EntityValidator
from .fact_validator import FactValidator
from .metrics import ValidationMetricsCalculator
from .numeric_validator import NumericValidator
from .schemas import (
    ClaimItem,
    CrossOutputConsistencyResult,
    EvidenceCoverageResult,
    FactSupportStatusEnum,
    IssueTypeEnum,
    SeverityEnum,
    ValidationContext,
    ValidationDecisionEnum,
    ValidationIssue,
    ValidationRequest,
    ValidationResult,
)
from .service import (
    ValidationService,
    get_validation_service,
    reset_validation_service,
)
from .structure import StructuralValidator
from .translation import TranslationValidator

__all__ = [
    "ValidationSettings",
    "get_validation_settings",
    "ClaimExtractor",
    "FactValidator",
    "EntityValidator",
    "NumericValidator",
    "CitationValidator",
    "ContradictionDetector",
    "EvidenceCoverageAnalyzer",
    "StructuralValidator",
    "TranslationValidator",
    "CrossOutputConsistencyEngine",
    "ValidationMetricsCalculator",
    "ValidationService",
    "get_validation_service",
    "reset_validation_service",
    "IssueTypeEnum",
    "SeverityEnum",
    "ValidationDecisionEnum",
    "FactSupportStatusEnum",
    "ClaimItem",
    "ValidationIssue",
    "EvidenceCoverageResult",
    "ValidationResult",
    "CrossOutputConsistencyResult",
    "ValidationContext",
    "ValidationRequest",
]
