"""Phase 12 Transformation Engine — Comprehensive Test Suite.

Verifies configuration, schemas, registry, profiles for all 15+ output types,
input adapter, prompt builder, model selection, Phase 9/10/11 integrations,
critical fact preservation, citation mapping validation, translation,
insufficient evidence handling, formatters, batch execution, and API endpoints.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.transformation.config import TransformationSettings, get_transformation_settings
from app.transformation.formatters import TransformationFormatter
from app.transformation.input_adapter import TransformationInputAdapter
from app.transformation.output_parser import TransformationOutputParser
from app.transformation.prompt_builder import TransformationPromptBuilder
from app.transformation.registry import TransformationRegistry, get_transformation_registry
from app.transformation.schemas import (
    EvidenceItem,
    OutputTypeEnum,
    TransformationPreviewResponse,
    TransformationProfile,
    TransformationRequest,
    TransformationResponse,
)
from app.transformation.service import (
    FallbackGenerationProvider,
    TransformationService,
    get_transformation_service,
)
from app.models.service import get_model_service
from app.models.config import ModelConfig
from app.models.base import BasePyTorchModel


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def service():
    return get_transformation_service()


@pytest.fixture
def sample_evidence():
    return [
        EvidenceItem(
            evidence_id="ev_001",
            document_id="doc_sec_report",
            content="Organization A announced Product B on 2026-01-10. Product B utilizes Technology C and is deployed in Region D.",
            score=0.95,
            source="Security Report 2026",
            page=2,
            chunk_id="chunk_04",
        ),
        EvidenceItem(
            evidence_id="ev_002",
            document_id="doc_audit_report",
            content="Product B achieved 99.9% uptime with 0 critical security incidents recorded.",
            score=0.88,
            source="Audit Report 2026",
            page=7,
            chunk_id="chunk_03",
        ),
    ]


# ---------------------------------------------------------------------------
# 1. Configuration Tests
# ---------------------------------------------------------------------------
def test_transformation_config():
    settings = get_transformation_settings()
    assert isinstance(settings, TransformationSettings)
    assert settings.enabled is True
    assert settings.default_output_type == "SUMMARY"
    assert settings.preserve_facts is True
    assert settings.strict_citations is True
    assert settings.max_context_length >= 256


# ---------------------------------------------------------------------------
# 2. Registry & Output Profile Tests (All 15+ Types)
# ---------------------------------------------------------------------------
def test_transformation_registry_profiles():
    registry = get_transformation_registry()
    profiles = registry.list_profiles()
    types = registry.list_output_types()

    # Verify at least 15 output types are registered
    assert len(profiles) >= 15
    assert len(types) >= 15

    expected_types = [
        "SUMMARY",
        "EXECUTIVE_SUMMARY",
        "QUICK_READ",
        "DETAILED_REPORT",
        "LINKEDIN_POST",
        "X_POST",
        "ADVISORY",
        "POLICY_BRIEF",
        "MEMO",
        "ANNOUNCEMENT",
        "VIDEO_SCRIPT",
        "PRESENTATION_OUTLINE",
        "INFOGRAPHIC_SPEC",
        "FAQ",
        "TRANSLATION",
        "EMAIL_COMMUNICATION",
        "STRUCTURED_REPORT",
    ]

    for t in expected_types:
        assert registry.validate_output_type(t) is True
        prof = registry.get_profile(t)
        assert isinstance(prof, TransformationProfile)
        assert prof.output_type == t
        assert len(prof.expected_structure) > 0


def test_invalid_output_type_lookup():
    registry = get_transformation_registry()
    assert registry.validate_output_type("INVALID_TYPE_123") is False
    with pytest.raises(KeyError):
        registry.get_profile("INVALID_TYPE_123")


# ---------------------------------------------------------------------------
# 3. Input Adapter & Context Creation Tests
# ---------------------------------------------------------------------------
def test_input_adapter(sample_evidence):
    adapter = TransformationInputAdapter()
    req = TransformationRequest(
        document_ids=["doc_sec_report"],
        evidence_items=sample_evidence,
        output_type="SUMMARY",
        audience="EXECUTIVES",
        tone="EXECUTIVE",
    )
    context = adapter.adapt(req)

    assert context.document_ids == ["doc_sec_report"]
    assert len(context.evidence_items) == 2
    assert len(context.citations) == 2
    assert context.citations[0].citation_id == "[1]"
    assert context.citations[0].evidence_id == "ev_001"
    assert context.citations[1].citation_id == "[2]"
    assert context.citations[1].evidence_id == "ev_002"
    assert context.insufficient_evidence is False


# ---------------------------------------------------------------------------
# 4. Prompt Builder Tests
# ---------------------------------------------------------------------------
def test_prompt_builder(sample_evidence):
    adapter = TransformationInputAdapter()
    builder = TransformationPromptBuilder()
    registry = get_transformation_registry()

    req = TransformationRequest(
        evidence_items=sample_evidence,
        output_type="EXECUTIVE_SUMMARY",
        audience="EXECUTIVES",
        tone="EXECUTIVE",
    )
    context = adapter.adapt(req)
    profile = registry.get_profile("EXECUTIVE_SUMMARY")
    prompt = builder.build_prompt(context, profile)

    assert "SYSTEM ROLE" in prompt
    assert "EXECUTIVE_SUMMARY" in prompt
    assert "ZERO HALLUCINATION" in prompt
    assert "PRESERVE NUMERICAL VALUES" in prompt
    assert "PRESERVE DATES" in prompt
    assert "[1]" in prompt
    assert "[2]" in prompt


# ---------------------------------------------------------------------------
# 5. Output Parser & Citation Validation Tests
# ---------------------------------------------------------------------------
def test_output_parser_citation_validation(sample_evidence):
    adapter = TransformationInputAdapter()
    parser = TransformationOutputParser()
    registry = get_transformation_registry()

    req = TransformationRequest(evidence_items=sample_evidence, output_type="SUMMARY")
    context = adapter.adapt(req)
    profile = registry.get_profile("SUMMARY")

    # Raw output with valid citations [1], [2] and an invalid/hallucinated citation [99]
    raw_output = """# Summary Header
## Overview
Organization A launched Product B on 2026-01-10 [1].

## Key Findings
Achieved 99.9% uptime with 0 incidents [2].
Fake claim from nonexistent source [99].
"""

    structured, warnings, matched_cits = parser.parse(raw_output, context, profile)

    assert structured.title == "Summary Header"
    assert len(structured.sections) == 2
    # Verify hallucinated citation [99] triggered a warning
    assert any("Hallucinated citation ID [99]" in w for w in warnings)
    # Verify matched valid citations
    matched_ids = {c.citation_id for c in matched_cits}
    assert "[1]" in matched_ids
    assert "[2]" in matched_ids
    assert "[99]" not in matched_ids


# ---------------------------------------------------------------------------
# 6. Critical Fact Preservation Test
# ---------------------------------------------------------------------------
def test_critical_fact_preservation(service, sample_evidence):
    req = TransformationRequest(
        evidence_items=sample_evidence,
        output_type="EXECUTIVE_SUMMARY",
        tone="PROFESSIONAL",
    )
    res = service.transform(req)

    assert res.status == "completed"
    assert res.insufficient_evidence is False

    # Verify exact facts are preserved in output
    assert "Organization A" in res.content
    assert "Product B" in res.content
    assert "2026-01-10" in res.content
    assert "Technology C" in res.content
    assert "Region D" in res.content
    assert "99.9%" in res.content

    # Negative check: Ensure facts were NOT mutated (e.g. 2026-01-10 not changed to 2026-01-11)
    assert "2026-01-11" not in res.content


# ---------------------------------------------------------------------------
# 7. Critical Citation Preservation & Mapping Test
# ---------------------------------------------------------------------------
def test_critical_citation_mapping(service, sample_evidence):
    req = TransformationRequest(
        evidence_items=sample_evidence,
        output_type="ADVISORY",
        citation_mode="INLINE",
    )
    res = service.transform(req)

    assert res.status == "completed"
    assert len(res.citations) == 2
    assert "ev_001" in res.evidence_ids
    assert "ev_002" in res.evidence_ids

    citation_ids = [c.citation_id for c in res.citations]
    assert "[1]" in citation_ids
    assert "[2]" in citation_ids
    assert "[99]" not in citation_ids


# ---------------------------------------------------------------------------
# 8. Critical Translation Test
# ---------------------------------------------------------------------------
def test_critical_translation_fact_preservation(service, sample_evidence):
    req = TransformationRequest(
        evidence_items=sample_evidence,
        output_type="TRANSLATION",
        language="en",
        target_language="es",
    )
    res = service.transform(req)

    assert res.status == "completed"
    assert res.output_type == "TRANSLATION"

    # Factual invariants must remain unchanged in translation
    assert "2026-01-10" in res.content
    assert "Product B" in res.content
    assert "Organization A" in res.content
    assert "[1]" in res.content


# ---------------------------------------------------------------------------
# 9. Output Profile Tests (Execution across all 15+ profiles)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "out_type",
    [
        "SUMMARY",
        "EXECUTIVE_SUMMARY",
        "QUICK_READ",
        "DETAILED_REPORT",
        "LINKEDIN_POST",
        "X_POST",
        "ADVISORY",
        "POLICY_BRIEF",
        "MEMO",
        "ANNOUNCEMENT",
        "VIDEO_SCRIPT",
        "PRESENTATION_OUTLINE",
        "INFOGRAPHIC_SPEC",
        "FAQ",
        "TRANSLATION",
        "EMAIL_COMMUNICATION",
        "STRUCTURED_REPORT",
    ],
)
def test_all_transformation_profiles_execution(service, sample_evidence, out_type):
    req = TransformationRequest(
        evidence_items=sample_evidence,
        output_type=out_type,
        audience="GENERAL_PUBLIC",
        tone="PROFESSIONAL",
    )
    res = service.transform(req)

    assert isinstance(res, TransformationResponse)
    assert res.output_type == out_type
    assert res.status == "completed"
    assert len(res.content) > 0
    assert res.latency_ms >= 0.0
    assert res.structured_content is not None
    assert len(res.structured_content.sections) > 0


# ---------------------------------------------------------------------------
# 10. Insufficient Evidence Test
# ---------------------------------------------------------------------------
def test_insufficient_evidence_handling(service):
    req = TransformationRequest(
        source_text="",
        evidence_items=[],
        output_type="SUMMARY",
    )
    res = service.transform(req)

    assert res.insufficient_evidence is True
    assert res.status == "insufficient_evidence"
    assert len(res.warnings) > 0
    assert any("no source content" in w.lower() for w in res.warnings)


# ---------------------------------------------------------------------------
# 11. Phase 9, 10, 11 Integration Tests
# ---------------------------------------------------------------------------
class DummyPyTorchModel(BasePyTorchModel):
    def predict(self, x):
        return x

    def predict_batch(self, batch):
        return batch


def test_phase9_and_phase11_model_integration(service, sample_evidence):
    # Register dummy PyTorch model in Phase 9 ModelRegistry
    model_service = get_model_service()
    dummy_config = ModelConfig(model_id="test_pytorch_transformer", model_name="Test Model")
    dummy_model = DummyPyTorchModel(config=dummy_config)
    model_service.registry.register(dummy_model)

    req = TransformationRequest(
        evidence_items=sample_evidence,
        output_type="SUMMARY",
        model_id="test_pytorch_transformer",
        model_type="pytorch",
        active_parameter_config={
            "selection_strategy": "top_k",
            "top_k": 2,
        },
    )
    res = service.transform(req)

    assert res.status == "completed"
    assert res.model_id == "test_pytorch_transformer"
    assert res.model_type == "pytorch"


# ---------------------------------------------------------------------------
# 12. Preview & Batch Transformation Tests
# ---------------------------------------------------------------------------
def test_preview_transformation(service):
    req = TransformationRequest(
        output_type="LINKEDIN_POST",
        audience="GENERAL_PUBLIC",
        active_parameter_config={"selection_strategy": "all"},
    )
    preview = service.preview_transformation(req)

    assert isinstance(preview, TransformationPreviewResponse)
    assert preview.output_type == "LINKEDIN_POST"
    assert "hook" in preview.expected_structure
    assert preview.active_parameter_metadata["configured"] is True


def test_batch_transformation(service, sample_evidence):
    reqs = [
        TransformationRequest(evidence_items=sample_evidence, output_type="SUMMARY"),
        TransformationRequest(evidence_items=sample_evidence, output_type="QUICK_READ"),
    ]
    results = service.transform_batch(reqs)

    assert len(results) == 2
    assert results[0].output_type == "SUMMARY"
    assert results[1].output_type == "QUICK_READ"


# ---------------------------------------------------------------------------
# 13. Formatter Tests
# ---------------------------------------------------------------------------
def test_transformation_formatters(service, sample_evidence):
    req = TransformationRequest(evidence_items=sample_evidence, output_type="SUMMARY")
    res = service.transform(req)

    md = TransformationFormatter.to_markdown(res)
    text = TransformationFormatter.to_plain_text(res)
    json_str = TransformationFormatter.to_json(res)

    assert md.startswith("#")
    assert "SUMMARY" in text
    assert '"transformation_id"' in json_str


# ---------------------------------------------------------------------------
# 14. API Endpoints Tests
# ---------------------------------------------------------------------------
def test_api_transformation_transform_endpoint(client, sample_evidence):
    payload = {
        "output_type": "EXECUTIVE_SUMMARY",
        "audience": "EXECUTIVES",
        "tone": "EXECUTIVE",
        "evidence_items": [item.model_dump() for item in sample_evidence],
    }
    response = client.post("/api/transformation/transform", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["output_type"] == "EXECUTIVE_SUMMARY"
    assert data["status"] == "completed"
    assert "content" in data
    assert "citations" in data


def test_api_transformation_types_endpoint(client):
    response = client.get("/api/transformation/types")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert "SUMMARY" in data
    assert "LINKEDIN_POST" in data


def test_api_transformation_profiles_endpoint(client):
    response = client.get("/api/transformation/profiles")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 15


def test_api_transformation_preview_endpoint(client):
    payload = {"output_type": "ADVISORY"}
    response = client.post("/api/transformation/preview", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["output_type"] == "ADVISORY"
    assert "expected_structure" in data
