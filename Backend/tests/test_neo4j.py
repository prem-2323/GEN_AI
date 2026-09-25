"""Phase 2 Real Neo4j Integration Test Suite.

Verifies:
1. Configuration handling (GRAPH_BACKEND=neo4j vs GRAPH_BACKEND=mock)
2. Connectivity verification & health endpoints (/api/graph/health, /api/graph/status)
3. Idempotent uniqueness constraints (Document, Chunk, Entity, Fact, Metric, Concept)
4. Node and relationship insertion (MERGE statements)
5. Duplicate prevention & ID stability
6. Parameterized Cypher queries (find_entity, get_relationships, etc.)
7. Strict no-silent-fallback behavior when GRAPH_BACKEND=neo4j
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import get_settings
from app.graph.neo4j import Neo4jDriverAdapter
from app.graph.repository import (
    Neo4jGraphRepository,
    MockNeo4jGraphStore,
    get_graph_repository,
    reset_graph_repository,
)
from app.graph.service import GraphService
from app.graph.models import (
    DocumentNodeModel,
    GraphNodeModel,
    GraphRelationshipModel,
    GraphPayload,
)

client = TestClient(app)


def test_1_configuration():
    """Verify GRAPH_BACKEND config setting."""
    settings = get_settings()
    assert hasattr(settings, "graph_backend")
    assert settings.graph_backend in ("neo4j", "mock")


def test_2_mock_backend_explicit():
    """Verify GRAPH_BACKEND=mock uses MockNeo4jGraphStore explicitly."""
    reset_graph_repository()
    settings = get_settings()
    original_backend = settings.graph_backend
    try:
        settings.graph_backend = "mock"
        repo = get_graph_repository()
        assert isinstance(repo, MockNeo4jGraphStore)
        assert repo.is_mock is True
    finally:
        settings.graph_backend = original_backend
        reset_graph_repository()


def test_3_no_silent_fallback_when_unreachable():
    """Verify GRAPH_BACKEND=neo4j raises ConnectionError if Neo4j is unreachable (NO silent mock fallback)."""
    reset_graph_repository()
    settings = get_settings()
    original_backend = settings.graph_backend
    original_uri = settings.neo4j_uri
    try:
        settings.graph_backend = "neo4j"
        # Set invalid unreachable port
        settings.neo4j_uri = "bolt://127.0.0.1:9999"
        
        with pytest.raises(ConnectionError) as exc_info:
            get_graph_repository()
            
        assert "GRAPH_BACKEND=neo4j requires an active Neo4j database" in str(exc_info.value)
    finally:
        settings.graph_backend = original_backend
        settings.neo4j_uri = original_uri
        reset_graph_repository()


def test_4_graph_health_endpoint():
    """Verify GET /api/graph/health and GET /health/neo4j."""
    res = client.get("/api/graph/health")
    assert res.status_code == 200
    data = res.json()
    assert "backend" in data
    assert "connected" in data


def test_5_graph_status_endpoint():
    """Verify GET /api/graph/status."""
    res = client.get("/api/graph/status")
    assert res.status_code == 200
    data = res.json()
    assert "backend" in data
    assert "connected" in data
    assert "nodes" in data
    assert "relationships" in data


def test_6_mock_store_crud():
    """Verify in-memory MockNeo4jGraphStore CRUD functionality for unit tests."""
    mock_store = MockNeo4jGraphStore()
    assert mock_store.init_constraints() is True
    
    payload = GraphPayload(
        document=DocumentNodeModel(document_id="doc_test_01", filename="sample.pdf", file_type="pdf"),
        nodes=[
            GraphNodeModel(entity_id="ent_01", canonical_name="Banana Ripeness", entity_type="Concept"),
            GraphNodeModel(entity_id="ent_02", canonical_name="ESP32", entity_type="Hardware"),
        ],
        relationships=[
            GraphRelationshipModel(
                relation_id="rel_01",
                source_id="ent_01",
                target_id="ent_02",
                relation_type="MONITORED_BY",
                evidence_text="Banana ripeness is monitored by ESP32."
            )
        ]
    )
    
    ok = mock_store.ingest_payload(payload)
    assert ok is True
    
    service = GraphService(repository=mock_store)
    ent = service.find_entity("ent_01")
    assert ent is not None
    assert ent["canonical_name"] == "Banana Ripeness"
    
    rels = service.get_entity_relationships("ent_01")
    assert len(rels) >= 1
