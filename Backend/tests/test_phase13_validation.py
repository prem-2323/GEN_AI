"""Phase 13 Validation & Consistency Engine — Comprehensive Test Suite.

Verifies schema validation, fact validation, entity checking, numeric/date matching,
citation verification, evidence coverage, contradiction detection, structural validation,
cross-output consistency, translation validation, decision policies, no factual auto-repair,
and API route execution.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.validation.config import ValidationSettings, get_validation_settings
from app.validation.schemas import (
    ClaimItem,
    CrossOutputConsistencyResult,
    FactSupportStatusEnum,
    IssueTypeEnum,
    SeverityEnum,
    ValidationContext,
    ValidationIssue,
    ValidationRequest,
    ValidationResult,
)
from app.validation.service import ValidationService, get_validation_service
from app.validation.fact_validator import FactValidator
from app.validation.entity_validator import EntityValidator
from app.validation.numeric_validator import NumericValidator
from app.validation.citation_validator import CitationValidator
from app.validation.claim_validator import ClaimExtractor
from app.validation.contradiction import ContradictionDetector
from app.validation.coverage import EvidenceCoverageAnalyzer
from app.validation.structure import StructuralValidator
from app.validation.translation import TranslationValidator
from app.validation.consistency import CrossOutputConsistencyEngine
from app.transformation.service import get_transformation_service
from app.transformation.schemas import EvidenceItem, TransformationRequest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def service():
    return get_validation_service()


@pytest.fixture
def trusted_evidence():
    return [
        {
            "evidence_id": "ev_001",
            "document_id": "doc_sec_report",
            "content": "Organization A announced Product B on 2026-01-10. Product B utilizes Technology C and is available in Region D.",
        },
        {
            "evidence_id": "ev_002",
            "document_id": "doc_audit_report",
            "content": "Product B budget is 25 million and achieved 99.9% uptime with 0 incidents recorded.",
        },
    ]


@pytest.fixture
def trusted_facts():
    return [
        {"subject": "Organization A", "predicate": "announced", "object_val": "Product B"},
        {"subject": "Product B", "predicate": "uses", "object_val": "Technology C"},
        {"subject": "Product B", "predicate": "available in", "object_val": "Region D"},
    ]


@pytest.fixture
def trusted_entities():
    return [
        {"name": "Organization A", "type": "ORGANIZATION"},
        {"name": "Product B", "type": "PRODUCT"},
        {"name": "Technology C", "type": "TECHNOLOGY"},
        {"name": "Region D", "type": "LOCATION"},
    ]


@pytest.fixture
def trusted_citations():
    return [
        {"citation_id": "[1]", "evidence_id": "ev_001", "document_id": "doc_sec_report"},
        {"citation_id": "[2]", "evidence_id": "ev_002", "document_id": "doc_audit_report"},
    ]


# ---------------------------------------------------------------------------
# 1. Configuration Tests
# ---------------------------------------------------------------------------
def test_validation_config():
    settings = get_validation_settings()
    assert isinstance(settings, ValidationSettings)
    assert settings.enabled is True
    assert settings.strict_dates is True
    assert settings.strict_numbers is True
    assert settings.strict_citations is True
    assert settings.allow_factual_auto_repair is False  # Must NEVER auto-rewrite factual values!


# ---------------------------------------------------------------------------
# 2. Critical Fact Preservation & Date Tests
# ---------------------------------------------------------------------------
def test_critical_fact_date_supported(service, trusted_evidence):
    req = ValidationRequest(
        transformation_output="Organization A announced Product B on 2026-01-10 [1].",
        evidence_items=trusted_evidence,
    )
    res = service.validate(req)
    assert res.status in ("PASS", "PASS_WITH_WARNINGS")
    assert res.passed is True
    assert not any(i.issue_type == IssueTypeEnum.DATE_MISMATCH for i in res.issues)


def test_critical_fact_date_mismatch(service, trusted_evidence):
    req = ValidationRequest(
        transformation_output="Organization A announced Product B on 2026-01-11 [1].",
        evidence_items=trusted_evidence,
    )
    res = service.validate(req)
    assert res.status == "FAIL"
    assert res.passed is False
    assert any(i.issue_type == IssueTypeEnum.DATE_MISMATCH for i in res.issues)


def test_critical_fact_date_contradiction(service, trusted_evidence):
    req = ValidationRequest(
        transformation_output="Product B was announced on 2026-01-15 [1].",
        evidence_items=trusted_evidence,
    )
    res = service.validate(req)
    assert res.status == "FAIL"
    assert any(i.issue_type in (IssueTypeEnum.DATE_MISMATCH, IssueTypeEnum.CONTRADICTION) for i in res.issues)


# ---------------------------------------------------------------------------
# 3. Critical Numeric Tests
# ---------------------------------------------------------------------------
def test_critical_numeric_supported(service, trusted_evidence):
    req = ValidationRequest(
        transformation_output="Product B budget is 25 million [2].",
        evidence_items=trusted_evidence,
    )
    res = service.validate(req)
    assert not any(i.issue_type == IssueTypeEnum.NUMBER_MISMATCH for i in res.issues)


def test_critical_numeric_mismatch(service, trusted_evidence):
    req = ValidationRequest(
        transformation_output="Product B budget is 250 million [2].",
        evidence_items=trusted_evidence,
    )
    res = service.validate(req)
    assert res.status == "FAIL"
    assert any(i.issue_type == IssueTypeEnum.NUMBER_MISMATCH for i in res.issues)


# ---------------------------------------------------------------------------
# 4. Critical Relation & Contradiction Tests
# ---------------------------------------------------------------------------
def test_critical_relation_contradiction(service, trusted_evidence, trusted_facts):
    req = ValidationRequest(
        transformation_output="Organization A does not use Technology C [1].",
        evidence_items=trusted_evidence,
        facts=trusted_facts,
    )
    res = service.validate(req)
    assert any(i.issue_type == IssueTypeEnum.CONTRADICTION for i in res.issues)


# ---------------------------------------------------------------------------
# 5. Critical Citation Validation Tests
# ---------------------------------------------------------------------------
def test_critical_citation_valid(service, trusted_evidence, trusted_citations):
    req = ValidationRequest(
        transformation_output="Product B utilizes Technology C [1].",
        evidence_items=trusted_evidence,
        citations=trusted_citations,
    )
    res = service.validate(req)
    assert not any(i.issue_type == IssueTypeEnum.CITATION_INVALID for i in res.issues)


def test_critical_citation_invalid_hallucinated(service, trusted_evidence, trusted_citations):
    req = ValidationRequest(
        transformation_output="Product B utilizes Technology C [99].",
        evidence_items=trusted_evidence,
        citations=trusted_citations,
    )
    res = service.validate(req)
    assert res.status == "FAIL"
    assert any(i.issue_type == IssueTypeEnum.CITATION_INVALID for i in res.issues)


# ---------------------------------------------------------------------------
# 6. Entity Validation & Canonical Normalization
# ---------------------------------------------------------------------------
def test_entity_validator_normalization():
    validator = EntityValidator()
    assert validator._normalize_name("OpenAI Inc.") == "openai"
    assert validator._normalize_name("OpenAI") == "openai"


def test_entity_validator_mismatch(service, trusted_evidence, trusted_entities):
    req = ValidationRequest(
        transformation_output="UnknownCompany announced Product B.",
        evidence_items=trusted_evidence,
        entities=trusted_entities,
    )
    res = service.validate(req)
    assert any(i.issue_type == IssueTypeEnum.ENTITY_MISMATCH for i in res.issues)


# ---------------------------------------------------------------------------
# 7. Structural Validation Tests
# ---------------------------------------------------------------------------
def test_structural_validation(service, trusted_evidence):
    req = ValidationRequest(
        transformation_output="# Executive Summary\nOverview text\n\n# Missing Section\nContent",
        evidence_items=trusted_evidence,
        output_type="ADVISORY",  # Requires situation, key_facts, recommended_actions
    )
    res = service.validate(req)
    assert any(i.issue_type == IssueTypeEnum.REQUIRED_FIELD_MISSING for i in res.issues)


# ---------------------------------------------------------------------------
# 8. Translation Factual Drift Tests
# ---------------------------------------------------------------------------
def test_translation_validation_drift(service, trusted_evidence):
    req = ValidationRequest(
        transformation_output="Product B announced without dates.",
        evidence_items=trusted_evidence,
        output_type="TRANSLATION",
    )
    res = service.validate(req)
    assert any(i.issue_type == IssueTypeEnum.TRANSLATION_DRIFT for i in res.issues)


# ---------------------------------------------------------------------------
# 9. Evidence Coverage Analyzer Tests
# ---------------------------------------------------------------------------
def test_evidence_coverage_analyzer(service, trusted_evidence):
    req = ValidationRequest(
        transformation_output="Organization A announced Product B on 2026-01-10 [1]. Product B utilizes Technology C [1]. Random unsupported statement xyz.",
        evidence_items=trusted_evidence,
    )
    res = service.validate(req)
    assert res.evidence_coverage.total_claims > 0
    assert 0.0 <= res.evidence_coverage.coverage_ratio <= 1.0


# ---------------------------------------------------------------------------
# 10. Cross-Output Consistency Tests
# ---------------------------------------------------------------------------
def test_cross_output_consistency_consistent(service):
    outputs = {
        "summary": "Product B was announced on 2026-01-10.",
        "linkedin": "Product B was announced on 2026-01-10.",
    }
    result = service.evaluate_consistency(outputs)
    assert isinstance(result, CrossOutputConsistencyResult)
    assert result.consistency_score == 1.0
    assert len(result.contradictions) == 0


def test_cross_output_consistency_inconsistent_date(service):
    outputs = {
        "summary": "Product B was announced on 2026-01-10.",
        "advisory": "Product B was announced on 2026-01-12.",
    }
    result = service.evaluate_consistency(outputs)
    assert result.consistency_score < 1.0
    assert "dates" in result.inconsistent_fields
    assert len(result.contradictions) > 0


# ---------------------------------------------------------------------------
# 11. No Factual Auto-Repair Test
# ---------------------------------------------------------------------------
def test_no_factual_auto_repair(service, trusted_evidence):
    req = ValidationRequest(
        transformation_output="  Product B was announced on 2026-01-11.  ",
        evidence_items=trusted_evidence,
    )
    res = service.validate(req)
    # Safe formatting repair trims outer spaces, but MUST NOT alter date 2026-01-11 to 2026-01-10!
    assert res.repaired_content == "Product B was announced on 2026-01-11."
    assert res.status == "FAIL"


# ---------------------------------------------------------------------------
# 12. API Endpoint Tests
# ---------------------------------------------------------------------------
def test_api_validation_validate_endpoint(client, trusted_evidence):
    payload = {
        "transformation_output": "Organization A announced Product B on 2026-01-10 [1].",
        "evidence_items": trusted_evidence,
        "output_type": "SUMMARY",
    }
    response = client.post("/api/validation/validate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "validation_id" in data
    assert "status" in data
    assert "evidence_coverage" in data


def test_api_validation_consistency_endpoint(client):
    payload = {
        "summary": "Product B was announced on 2026-01-10.",
        "advisory": "Product B was announced on 2026-01-12.",
    }
    response = client.post("/api/validation/consistency", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "consistency_score" in data
    assert "inconsistent_fields" in data


# ---------------------------------------------------------------------------
# 13. Additional Granular Unit Tests (Prompt Items 1-35 Coverage)
# ---------------------------------------------------------------------------
def test_claim_extraction_structure():
    extractor = ClaimExtractor()
    ctx = ValidationContext(transformation_output="Organization A announced Product B on 2026-01-10 [1]. Budget is 25 million [2].")
    claims = extractor.extract_claims(ctx)
    assert len(claims) >= 2
    assert any(c.date_val == "2026-01-10" for c in claims)
    assert any("25 million" in (c.number_val or "") for c in claims)


def test_fact_supported_classification(trusted_evidence):
    validator = FactValidator()
    claims = [ClaimItem(text="Organization A announced Product B on 2026-01-10.")]
    ctx = ValidationContext(source_evidence=trusted_evidence, transformation_output="")
    issues, statuses = validator.validate_facts(claims, ctx)
    assert statuses[0] == FactSupportStatusEnum.SUPPORTED


def test_fact_unsupported_classification(trusted_evidence):
    validator = FactValidator()
    claims = [ClaimItem(text="Quantum teleportation was invented in Atlantis.")]
    ctx = ValidationContext(source_evidence=trusted_evidence, transformation_output="")
    issues, statuses = validator.validate_facts(claims, ctx)
    assert statuses[0] == FactSupportStatusEnum.UNSUPPORTED


def test_numeric_normalization_equivalence():
    validator = NumericValidator()
    assert validator._normalize_number("25 million") == 25000000.0
    assert validator._normalize_number("25,000,000") == 25000000.0
    assert validator._normalize_number("25M") == 25000000.0


def test_numeric_mismatch_different_values():
    validator = NumericValidator()
    ctx = ValidationContext(
        source_evidence=[{"content": "Budget is 25 million."}],
        transformation_output="Budget is 35 million.",
    )
    num_issues, date_issues = validator.validate_numerics_and_dates(ctx)
    assert len(num_issues) > 0
    assert num_issues[0].issue_type == IssueTypeEnum.NUMBER_MISMATCH


def test_citation_missing_warning(trusted_citations):
    validator = CitationValidator()
    ctx = ValidationContext(
        citations=trusted_citations,
        transformation_output="Product B is a technology product without citation tags.",
    )
    issues, cit_map = validator.validate_citations(ctx)
    assert any(i.issue_type == IssueTypeEnum.CITATION_MISSING for i in issues)


def test_evidence_coverage_zero_claims():
    analyzer = EvidenceCoverageAnalyzer()
    res = analyzer.analyze_coverage([])
    assert res.coverage_ratio == 1.0
    assert res.total_claims == 0


def test_contradiction_negation_detection(trusted_evidence, trusted_facts):
    detector = ContradictionDetector()
    ctx = ValidationContext(
        source_evidence=trusted_evidence,
        source_facts=trusted_facts,
        transformation_output="Product B does not use Technology C.",
    )
    issues = detector.detect_contradictions(ctx)
    assert len(issues) > 0
    assert issues[0].issue_type == IssueTypeEnum.CONTRADICTION


def test_pass_with_warnings_decision(service, trusted_evidence, trusted_citations):
    req = ValidationRequest(
        transformation_output="Organization A announced Product B on 2026-01-10. Product B utilizes Technology C.",  # Missing citations -> Warning
        evidence_items=trusted_evidence,
        citations=trusted_citations,
    )
    res = service.validate(req)
    assert res.status == "PASS_WITH_WARNINGS"
    assert res.passed is True
    assert len(res.warnings) > 0


def test_fail_decision_on_critical_error(service, trusted_evidence):
    req = ValidationRequest(
        transformation_output="Organization A announced Product B on 2026-01-15.",  # Wrong date -> FAIL
        evidence_items=trusted_evidence,
    )
    res = service.validate(req)
    assert res.status == "FAIL"
    assert res.passed is False


def test_empty_output_handling(service, trusted_evidence):
    req = ValidationRequest(
        transformation_output="",
        evidence_items=trusted_evidence,
    )
    res = service.validate(req)
    assert isinstance(res, ValidationResult)


def test_missing_evidence_handling(service):
    req = ValidationRequest(
        transformation_output="Product B is a product.",
        evidence_items=[],
    )
    res = service.validate(req)
    assert isinstance(res, ValidationResult)


def test_source_immutability(service, trusted_evidence):
    original_evidence_content = trusted_evidence[0]["content"]
    req = ValidationRequest(
        transformation_output="Product B was announced on 2026-01-15.",
        evidence_items=trusted_evidence,
    )
    service.validate(req)
    # Ground truth evidence content MUST remain immutable
    assert trusted_evidence[0]["content"] == original_evidence_content


def test_multiple_documents_handling(service):
    multi_evidence = [
        {"evidence_id": "e1", "document_id": "doc_A", "content": "Organization A released Product B on 2026-01-10."},
        {"evidence_id": "e2", "document_id": "doc_B", "content": "Product B utilizes Technology C in Region D."},
    ]
    req = ValidationRequest(
        transformation_output="Organization A released Product B on 2026-01-10 [1]. Product B utilizes Technology C [2].",
        evidence_items=multi_evidence,
    )
    res = service.validate(req)
    assert res.status in ("PASS", "PASS_WITH_WARNINGS")


def test_duplicate_claims_handling(service, trusted_evidence):
    req = ValidationRequest(
        transformation_output="Product B is available in Region D [1]. Product B is available in Region D [1].",
        evidence_items=trusted_evidence,
    )
    res = service.validate(req)
    assert isinstance(res, ValidationResult)


def test_duplicate_citations_handling(service, trusted_evidence, trusted_citations):
    req = ValidationRequest(
        transformation_output="Product B utilizes Technology C [1] [1].",
        evidence_items=trusted_evidence,
        citations=trusted_citations,
    )
    res = service.validate(req)
    assert not any(i.issue_type == IssueTypeEnum.CITATION_INVALID for i in res.issues)


def test_phase12_integration_with_validation(service):
    transform_service = get_transformation_service()
    evidence = [EvidenceItem(evidence_id="ev_001", document_id="doc1", content="Organization A announced Product B on 2026-01-10.")]
    t_req = TransformationRequest(
        evidence_items=evidence,
        output_type="SUMMARY",
    )
    t_res = transform_service.transform(t_req)

    v_req = ValidationRequest(
        transformation_output=t_res.content,
        evidence_items=[{"evidence_id": "ev_001", "document_id": "doc1", "content": "Organization A announced Product B on 2026-01-10."}],
        citations=[c.model_dump() for c in t_res.citations],
        output_type=t_res.output_type,
    )
    v_res = service.validate(v_req)
    assert v_res.passed is True, f"Validation failed with issues: {[f'{i.issue_type}({i.severity}): {i.message}' for i in v_res.issues]}"
