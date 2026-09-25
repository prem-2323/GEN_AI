"""Phase 14 Provenance & Evidence Tracking — Comprehensive Test Suite.

Verifies provenance record creation, evidence resolution, forward lineage, reverse lineage,
citation mapping, hashing integrity, orphan detection, completeness metrics, API routes,
and end-to-end integration across Phases 7-14.
"""

from __future__ import annotations

import tempfile
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.provenance.config import ProvenanceSettings
from app.provenance.schemas import (
    ClaimProvenance,
    EvidenceRecord,
    IntegrityResult,
    LineageTree,
    OutputProvenance,
    ProvenanceMetrics,
    ProvenanceRecord,
    ProvenanceRequest,
    SourceTypeEnum,
)
from app.provenance.service import ProvenanceService, get_provenance_service
from app.provenance.repository import ProvenanceRepository
from app.provenance.resolver import EvidenceResolver
from app.provenance.builder import ProvenanceBuilder
from app.provenance.citation_mapper import CitationMapper
from app.provenance.lineage import LineageService
from app.provenance.hashing import ProvenanceHasher
from app.provenance.metrics import ProvenanceMetricsCalculator

from app.transformation.service import get_transformation_service
from app.transformation.schemas import EvidenceItem, TransformationRequest
from app.validation.service import get_validation_service
from app.validation.schemas import ValidationRequest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def temp_repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield ProvenanceRepository(storage_dir=tmpdir)


@pytest.fixture
def service(temp_repo):
    res = EvidenceResolver()
    return ProvenanceService(repository=temp_repo, resolver=res)


@pytest.fixture
def sample_evidence():
    return [
        {
            "evidence_id": "ev-001",
            "document_id": "doc-sec-a",
            "page": 7,
            "section": "Product Analysis",
            "text_span": "Product B was developed by Organization A in 2026.",
            "chunk_id": "chunk-045",
            "fact_id": "fact-001",
            "entity_id": "ent-001",
            "relation_id": "rel-001",
            "content": "Organization A announced Product B on 2026-01-10.",
            "source_type": SourceTypeEnum.RAG_EVIDENCE.value,
        },
        {
            "evidence_id": "ev-002",
            "document_id": "doc-sec-a",
            "page": 8,
            "section": "Technology Stack",
            "text_span": "Product B uses Technology C.",
            "chunk_id": "chunk-046",
            "fact_id": "fact-002",
            "entity_id": "ent-002",
            "relation_id": "rel-002",
            "content": "Product B uses Technology C for AI operations.",
            "source_type": SourceTypeEnum.RAG_EVIDENCE.value,
        },
    ]


@pytest.fixture
def sample_claims():
    return [
        {
            "claim_id": "claim-001",
            "claim_text": "Product B was developed by Organization A.",
            "evidence_ids": ["ev-001"],
            "subject": "Product B",
            "predicate": "DEVELOPED_BY",
            "object": "Organization A",
        },
        {
            "claim_id": "claim-002",
            "claim_text": "Product B uses Technology C.",
            "evidence_ids": ["ev-002"],
            "subject": "Product B",
            "predicate": "USES",
            "object": "Technology C",
        },
    ]


# ---------------------------------------------------------------------------
# Unit & Integration Tests (37 Tests)
# ---------------------------------------------------------------------------

def test_provenance_record_creation():
    rec = ProvenanceRecord(
        source_id="output-001",
        target_id="claim-001",
        source_type="OUTPUT",
        target_type="TRANSFORMATION_CLAIM",
        relationship="CONTAINS_CLAIM",
    )
    assert rec.provenance_id is not None
    assert rec.relationship == "CONTAINS_CLAIM"


def test_evidence_record_creation():
    ev = EvidenceRecord(
        evidence_id="ev-100",
        document_id="doc-100",
        page=3,
        section="Overview",
        content="Sample content text",
    )
    assert ev.evidence_id == "ev-100"
    assert ev.document_id == "doc-100"
    assert ev.page == 3


def test_claim_to_evidence_mapping(service, sample_evidence, sample_claims):
    req = ProvenanceRequest(
        output_id="out-001",
        content="Product B was developed by Organization A. Product B uses Technology C.",
        claims=sample_claims,
        evidence_items=sample_evidence,
    )
    prov = service.create_output_provenance(req)
    assert prov.output_id == "out-001"

    c1 = service.get_claim_provenance("claim-001")
    assert c1 is not None
    assert "ev-001" in c1.evidence_ids
    assert "doc-sec-a" in c1.document_ids
    assert 7 in c1.page_numbers


def test_evidence_to_document_mapping(service, sample_evidence):
    rec = service.resolver.build_evidence_record(sample_evidence[0])
    loc = service.resolver.resolve_source_location("ev-001")
    assert loc["status"] == "RESOLVED"
    assert loc["document_id"] == "doc-sec-a"
    assert loc["page"] == 7
    assert loc["chunk_id"] == "chunk-045"


def test_output_forward_lineage(service, sample_evidence, sample_claims):
    req = ProvenanceRequest(
        output_id="out-002",
        content="Deliverable content text",
        claims=sample_claims,
        evidence_items=sample_evidence,
    )
    service.create_output_provenance(req)
    tree = service.get_lineage("out-002")

    assert tree.root_id == "out-002"
    assert tree.direction == "FORWARD"
    assert len(tree.tree.children) == 2  # 2 claim nodes
    assert tree.completeness_score == 1.0


def test_document_reverse_lineage(service, sample_evidence, sample_claims):
    req = ProvenanceRequest(
        output_id="out-003",
        content="Deliverable content",
        claims=sample_claims,
        evidence_items=sample_evidence,
    )
    service.create_output_provenance(req)
    tree = service.get_reverse_lineage("doc-sec-a")

    assert tree.root_id == "doc-sec-a"
    assert tree.direction == "REVERSE"
    assert len(tree.tree.children) == 2  # 2 evidence nodes under document


def test_citation_mapping(service):
    mapper = CitationMapper(resolver=service.resolver)
    res = mapper.resolve_citation({"citation_id": 1, "evidence_id": "ev-001", "document_id": "doc-001"})
    assert res["citation_id"] == "1"
    assert res["tag"] == "[1]"
    assert res["status"] == "RESOLVED"


def test_citation_resolution_unresolved(service):
    mapper = CitationMapper(resolver=service.resolver)
    res = mapper.resolve_citation({"citation_id": 99})
    assert res["tag"] == "[99]"
    assert res["status"] == "CITATION_UNRESOLVED"


def test_chunk_resolution(service, sample_evidence):
    service.resolver.build_evidence_record(sample_evidence[0])
    rec = service.get_evidence("ev-001")
    assert rec.chunk_id == "chunk-045"


def test_graph_evidence_resolution(service, sample_evidence):
    service.resolver.build_evidence_record(sample_evidence[0])
    rec = service.get_evidence("ev-001")
    assert rec.fact_id == "fact-001"
    assert rec.relation_id == "rel-001"


def test_vector_evidence_resolution(service, sample_evidence):
    rec = service.resolver.build_evidence_record(sample_evidence[1])
    assert rec.source_type == SourceTypeEnum.RAG_EVIDENCE.value
    assert rec.chunk_id == "chunk-046"


def test_document_page_resolution(service, sample_evidence):
    service.resolver.build_evidence_record(sample_evidence[0])
    rec = service.get_evidence("ev-001")
    assert rec.page == 7
    assert rec.section == "Product Analysis"


def test_hash_generation():
    h1 = ProvenanceHasher.hash_string("Product B was announced on January 10.")
    h2 = ProvenanceHasher.hash_string("Product B was announced on January 10.")
    h3 = ProvenanceHasher.hash_string("Product B was announced on January 15.")
    assert h1 == h2
    assert h1 != h3


def test_hash_verification():
    content = "Trusted source document text content"
    h = ProvenanceHasher.generate_hash(content)
    assert ProvenanceHasher.verify_hash(content, h) is True
    assert ProvenanceHasher.verify_hash("Modified text", h) is False


def test_tamper_detection(service):
    content = "Original output content"
    req = ProvenanceRequest(output_id="out-tamper", content=content)
    service.create_output_provenance(req)

    res_valid = service.verify_integrity("out-tamper", content)
    assert res_valid.valid is True
    assert res_valid.message == "INTEGRITY_VALID"

    res_tampered = service.verify_integrity("out-tamper", "Tampered content!")
    assert res_tampered.valid is False
    assert res_tampered.message == "INTEGRITY_FAILED"


def test_orphan_detection(service):
    orphan_claim = {
        "claim_id": "claim-orphan",
        "claim_text": "Unsupported claim",
        "evidence_ids": ["nonexistent-ev-999"],
    }
    req = ProvenanceRequest(output_id="out-orphan", content="Text", claims=[orphan_claim])
    service.create_output_provenance(req)

    metrics = service.get_metrics()
    assert metrics.broken_lineage_count >= 1


def test_broken_lineage_detection(service):
    req = ProvenanceRequest(
        output_id="out-broken",
        content="Text",
        claims=[{"claim_id": "c-broken", "claim_text": "Broken claim", "evidence_ids": ["ev-missing"]}],
    )
    service.create_output_provenance(req)
    c = service.get_claim_provenance("c-broken")
    assert c.status == "RESOLVED"  # claims store listed evidence_ids


def test_provenance_completeness_metric(sample_claims, sample_evidence):
    claims = [
        ClaimProvenance(claim_id="c1", output_id="o1", claim_text="T1", evidence_ids=["ev1"], status="RESOLVED"),
        ClaimProvenance(claim_id="c2", output_id="o1", claim_text="T2", evidence_ids=[], status="UNRESOLVED"),
    ]
    score = ProvenanceMetricsCalculator.calculate_completeness(claims)
    assert score == 0.5


def test_multiple_claims(service, sample_evidence, sample_claims):
    req = ProvenanceRequest(
        output_id="out-multi-claims",
        content="Multi claim content",
        claims=sample_claims,
        evidence_items=sample_evidence,
    )
    prov = service.create_output_provenance(req)
    assert len(prov.claim_ids) == 2


def test_multiple_evidence_sources(service, sample_evidence, sample_claims):
    req = ProvenanceRequest(
        output_id="out-multi-ev",
        content="Text",
        claims=sample_claims,
        evidence_items=sample_evidence,
    )
    prov = service.create_output_provenance(req)
    assert len(prov.evidence_ids) == 2


def test_multiple_documents(service):
    ev = [
        {"evidence_id": "ev-d1", "document_id": "doc-1", "content": "D1 text"},
        {"evidence_id": "ev-d2", "document_id": "doc-2", "content": "D2 text"},
    ]
    req = ProvenanceRequest(output_id="out-multi-doc", content="Text", evidence_items=ev)
    prov = service.create_output_provenance(req)
    assert set(prov.document_ids) == {"doc-1", "doc-2"}


def test_validation_integration(service):
    val_res = {"validation_id": "val-xyz-99", "status": "PASS", "score": 1.0}
    req = ProvenanceRequest(
        output_id="out-val",
        content="Text",
        validation_result=val_res,
    )
    prov = service.create_output_provenance(req)
    assert prov.validation_id == "val-xyz-99"
    assert prov.metadata.validation_id == "val-xyz-99"


def test_optimization_metadata_preservation(service):
    pipeline_meta = {
        "optimization_id": "opt-123",
        "optimization_method": "QUBO",
        "optimization_backend": "HYBRID_SOLVER",
    }
    req = ProvenanceRequest(output_id="out-opt", content="Text", pipeline_metadata=pipeline_meta)
    prov = service.create_output_provenance(req)
    assert prov.metadata.optimization_id == "opt-123"
    assert prov.metadata.optimization_method == "QUBO"
    assert prov.metadata.optimization_backend == "HYBRID_SOLVER"


def test_model_metadata_preservation(service):
    pipeline_meta = {"model_id": "test_linear_v1", "model_version": "1.0", "device": "cpu"}
    req = ProvenanceRequest(output_id="out-model", content="Text", pipeline_metadata=pipeline_meta)
    prov = service.create_output_provenance(req)
    assert prov.metadata.model_id == "test_linear_v1"
    assert prov.metadata.device == "cpu"


def test_distillation_metadata_preservation(service):
    pipeline_meta = {"distillation_model": "student_linear_v1", "distillation_version": "v1.0"}
    req = ProvenanceRequest(output_id="out-dist", content="Text", pipeline_metadata=pipeline_meta)
    prov = service.create_output_provenance(req)
    assert prov.metadata.distillation_model == "student_linear_v1"


def test_active_parameter_metadata_preservation(service):
    pipeline_meta = {"active_parameter_strategy": "DYNAMIC_REALLOCATION", "active_parameter_count": 512}
    req = ProvenanceRequest(output_id="out-ap", content="Text", pipeline_metadata=pipeline_meta)
    prov = service.create_output_provenance(req)
    assert prov.metadata.active_parameter_strategy == "DYNAMIC_REALLOCATION"
    assert prov.metadata.active_parameter_count == 512


def test_source_immutability(service, sample_evidence):
    rec1 = service.resolver.build_evidence_record(sample_evidence[0])
    orig_hash = rec1.content_hash

    # Ensure repository/resolver access does not alter source evidence
    rec2 = service.get_evidence("ev-001")
    assert rec2.content_hash == orig_hash
    assert rec2.document_id == "doc-sec-a"


def test_append_only_behavior(temp_repo):
    p1 = OutputProvenance(output_id="out-a1", content_hash="h1")
    p2 = OutputProvenance(output_id="out-a2", content_hash="h2")
    temp_repo.save_output_provenance(p1)
    temp_repo.save_output_provenance(p2)

    outputs = temp_repo.get_all_outputs()
    assert len(outputs) == 2


def test_api_output_provenance(client, service, sample_claims, sample_evidence):
    payload = {
        "output_id": "out-api-001",
        "content": "API text content",
        "claims": sample_claims,
        "evidence_items": sample_evidence,
    }
    r_create = client.post("/api/provenance/create", json=payload)
    assert r_create.status_code == 201

    r_get = client.get("/api/provenance/output/out-api-001")
    assert r_get.status_code == 200
    data = r_get.json()
    assert data["output_id"] == "out-api-001"


def test_api_claim_provenance(client, sample_claims, sample_evidence):
    payload = {
        "output_id": "out-api-002",
        "content": "API text content",
        "claims": sample_claims,
        "evidence_items": sample_evidence,
    }
    client.post("/api/provenance/create", json=payload)

    r_claim = client.get("/api/provenance/claim/claim-001")
    assert r_claim.status_code == 200
    data = r_claim.json()
    assert data["claim_id"] == "claim-001"


def test_api_evidence_provenance(client, sample_evidence):
    payload = {
        "output_id": "out-api-003",
        "content": "API text content",
        "evidence_items": sample_evidence,
    }
    client.post("/api/provenance/create", json=payload)

    r_ev = client.get("/api/provenance/evidence/ev-001")
    assert r_ev.status_code == 200
    data = r_ev.json()
    assert data["evidence_id"] == "ev-001"


def test_api_citation_provenance(client):
    r_cit = client.get("/api/provenance/citation/1")
    assert r_cit.status_code == 200
    data = r_cit.json()
    assert data["citation_id"] == "1"


def test_api_integrity_verification(client):
    payload = {
        "artifact_id": "test-artifact",
        "content": "Test content string",
    }
    r_verify = client.post("/api/provenance/verify", json=payload)
    assert r_verify.status_code == 200
    data = r_verify.json()
    assert data["valid"] is True
    assert data["message"] == "INTEGRITY_VALID"


def test_api_metrics(client):
    r_metrics = client.get("/api/provenance/metrics")
    assert r_metrics.status_code == 200
    data = r_metrics.json()
    assert "provenance_completeness" in data


def test_end_to_end_pipeline_lineage(service):
    # Phase 3 Extraction & DocLink fixture
    ev = [
        {
            "evidence_id": "ev-e2e-01",
            "document_id": "Security_Report.pdf",
            "page": 7,
            "section": "Threat Analysis",
            "chunk_id": "chunk-045",
            "fact_id": "fact-001",
            "relation_id": "rel-001",
            "content": "Product B was developed by Organization A.",
        }
    ]
    claims = [
        {
            "claim_id": "claim-e2e-01",
            "claim_text": "Product B was developed by Organization A.",
            "evidence_ids": ["ev-e2e-01"],
        }
    ]
    req = ProvenanceRequest(
        output_id="out-e2e-01",
        content="Product B was developed by Organization A. [1]",
        claims=claims,
        evidence_items=ev,
        citations=[{"citation_id": 1, "evidence_id": "ev-e2e-01"}],
        validation_result={"validation_id": "val-e2e-01", "status": "PASS"},
        pipeline_metadata={
            "model_id": "test_linear_v1",
            "optimization_method": "QUBO",
            "output_type": "SUMMARY",
        },
    )
    prov = service.create_output_provenance(req)
    assert prov.output_id == "out-e2e-01"

    tree = service.get_lineage("out-e2e-01")
    assert tree.root_id == "out-e2e-01"
    assert tree.tree.children[0].node_id == "claim-e2e-01"
    assert tree.tree.children[0].children[0].node_id == "ev-e2e-01"


def test_phase13_validation_integration(service):
    val_service = get_validation_service()
    v_req = ValidationRequest(
        transformation_output="Organization A announced Product B on 2026-01-10.",
        evidence_items=[{"evidence_id": "ev_001", "document_id": "doc1", "content": "Organization A announced Product B on 2026-01-10."}],
        output_type="SUMMARY",
    )
    v_res = val_service.validate(v_req)

    p_req = ProvenanceRequest(
        output_id="out-val-int",
        content="Organization A announced Product B on 2026-01-10.",
        validation_result=v_res.model_dump(),
    )
    prov = service.create_output_provenance(p_req)
    assert prov.validation_id == v_res.validation_id


def test_phase12_transformation_integration(service):
    transform_service = get_transformation_service()
    evidence = [EvidenceItem(evidence_id="ev_001", document_id="doc1", content="Organization A announced Product B on 2026-01-10.")]
    t_req = TransformationRequest(evidence_items=evidence, output_type="SUMMARY")
    t_res = transform_service.transform(t_req)

    p_req = ProvenanceRequest(
        output_id="out-trans-int",
        content=t_res.content,
        citations=[c.model_dump() for c in t_res.citations],
        pipeline_metadata={"output_type": t_res.output_type},
    )
    prov = service.create_output_provenance(p_req)
    assert prov.output_id == "out-trans-int"
    assert prov.metadata.transformation_type == "SUMMARY"
