"""Phase 13 Validation & Consistency Engine — Service Orchestrator.

Orchestrates full validation pipeline across claim extraction, fact validation,
entity checking, date/numeric validation, citation verification, evidence coverage,
contradiction detection, structural checks, translation drift, and cross-output consistency.
"""

from __future__ import annotations

import time
import uuid
import logging
from typing import Dict, List, Optional

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
    CrossOutputConsistencyResult,
    FactSupportStatusEnum,
    SeverityEnum,
    ValidationContext,
    ValidationIssue,
    ValidationRequest,
    ValidationResult,
)
from .structure import StructuralValidator
from .translation import TranslationValidator

log = logging.getLogger("gen-transform.validation.service")


class ValidationService:
    """Core Validation Service orchestrator."""

    def __init__(
        self,
        config: Optional[ValidationSettings] = None,
        claim_extractor: Optional[ClaimExtractor] = None,
        fact_validator: Optional[FactValidator] = None,
        entity_validator: Optional[EntityValidator] = None,
        numeric_validator: Optional[NumericValidator] = None,
        citation_validator: Optional[CitationValidator] = None,
        contradiction_detector: Optional[ContradictionDetector] = None,
        coverage_analyzer: Optional[EvidenceCoverageAnalyzer] = None,
        structural_validator: Optional[StructuralValidator] = None,
        translation_validator: Optional[TranslationValidator] = None,
        consistency_engine: Optional[CrossOutputConsistencyEngine] = None,
    ) -> None:
        self.config = config or get_validation_settings()
        self.claim_extractor = claim_extractor or ClaimExtractor()
        self.fact_validator = fact_validator or FactValidator()
        self.entity_validator = entity_validator or EntityValidator()
        self.numeric_validator = numeric_validator or NumericValidator()
        self.citation_validator = citation_validator or CitationValidator()
        self.contradiction_detector = contradiction_detector or ContradictionDetector()
        self.coverage_analyzer = coverage_analyzer or EvidenceCoverageAnalyzer()
        self.structural_validator = structural_validator or StructuralValidator()
        self.translation_validator = translation_validator or TranslationValidator()
        self.consistency_engine = consistency_engine or CrossOutputConsistencyEngine()

    def build_context(self, request: ValidationRequest) -> ValidationContext:
        """Construct ValidationContext from API request."""
        expected_structure = []
        try:
            from ..transformation.registry import get_transformation_registry
            registry = get_transformation_registry()
            if registry.validate_output_type(request.output_type):
                profile = registry.get_profile(request.output_type)
                expected_structure = profile.expected_structure
        except Exception:
            pass

        return ValidationContext(
            document_ids=[item.get("document_id", "") for item in request.evidence_items if item.get("document_id")],
            source_evidence=request.evidence_items,
            source_facts=request.facts,
            source_entities=request.entities,
            source_relations=request.relations,
            citations=request.citations,
            transformation_output=request.transformation_output,
            structured_output=request.structured_output,
            output_type=request.output_type,
            language=request.language,
            expected_structure=expected_structure,
        )

    def validate(self, request: ValidationRequest) -> ValidationResult:
        """Execute complete Phase 13 Validation Pipeline."""
        start_time = time.perf_counter()
        validation_id = str(uuid.uuid4())
        context = self.build_context(request)

        issues: List[ValidationIssue] = []

        # 1. Claim Extraction
        claims = self.claim_extractor.extract_claims(context)

        # 2. Fact Validation & Coverage
        fact_issues, support_statuses = self.fact_validator.validate_facts(claims, context)
        issues.extend(fact_issues)
        coverage_result = self.coverage_analyzer.analyze_coverage(support_statuses)

        # 3. Entity Validation
        entity_issues = self.entity_validator.validate_entities(context)
        issues.extend(entity_issues)

        # 4. Numeric & Date Validation
        numeric_issues, date_issues = self.numeric_validator.validate_numerics_and_dates(context)
        issues.extend(numeric_issues)
        issues.extend(date_issues)

        # 5. Citation Validation
        citation_issues, cit_map = self.citation_validator.validate_citations(context)
        issues.extend(citation_issues)

        # 6. Contradiction Detection
        contradiction_issues = self.contradiction_detector.detect_contradictions(context)
        issues.extend(contradiction_issues)

        # 7. Structural Validation
        structural_issues = self.structural_validator.validate_structure(context)
        issues.extend(structural_issues)

        # 8. Translation Validation
        translation_issues = self.translation_validator.validate_translation(context)
        issues.extend(translation_issues)

        # 9. Metrics & Categorization
        categorized = ValidationMetricsCalculator.categorize_issues(issues)
        warnings = categorized["warnings"]
        errors = categorized["errors"]

        score = ValidationMetricsCalculator.calculate_score(issues)

        # 10. Policy Decision
        checks_run = 8
        checks_failed = len(set(i.issue_type for i in issues))
        checks_passed = max(0, checks_run - checks_failed)

        status = "PASS"
        passed = True

        if errors:
            status = "FAIL"
            passed = False
        elif warnings:
            status = "PASS_WITH_WARNINGS"
            passed = True

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # Safe formatting repair if enabled (CRITICAL: never auto-rewrite factual values)
        repaired_text: Optional[str] = None
        if self.config.enable_safe_formatting_repair and not self.config.allow_factual_auto_repair:
            # Strip trailing double spaces or whitespace
            repaired_text = context.transformation_output.strip()

        return ValidationResult(
            validation_id=validation_id,
            transformation_id=request.transformation_id,
            status=status,
            passed=passed,
            score=score,
            issues=issues,
            warnings=warnings,
            errors=errors,
            checks_run=checks_run,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            evidence_coverage=coverage_result,
            citation_validity={
                "valid_count": len(cit_map),
                "citations_map": cit_map,
            },
            consistency_score=score,
            validation_latency_ms=round(latency_ms, 2),
            repaired_content=repaired_text,
        )

    def evaluate_consistency(
        self, outputs: Dict[str, str]
    ) -> CrossOutputConsistencyResult:
        """Evaluate cross-output consistency across multiple deliverables."""
        return self.consistency_engine.evaluate_cross_output_consistency(outputs)


_VALIDATION_SERVICE_INSTANCE: Optional[ValidationService] = None


def get_validation_service() -> ValidationService:
    """Return singleton instance of ValidationService."""
    global _VALIDATION_SERVICE_INSTANCE
    if _VALIDATION_SERVICE_INSTANCE is None:
        _VALIDATION_SERVICE_INSTANCE = ValidationService()
    return _VALIDATION_SERVICE_INSTANCE


def reset_validation_service() -> None:
    """Reset singleton instance of ValidationService."""
    global _VALIDATION_SERVICE_INSTANCE
    _VALIDATION_SERVICE_INSTANCE = None


__all__ = [
    "ValidationService",
    "get_validation_service",
    "reset_validation_service",
]
