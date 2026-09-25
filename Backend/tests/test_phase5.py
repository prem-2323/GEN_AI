import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.doclink.service import DocLinkService
from app.graph.service import GraphService
from app.graph.mapper import map_doclink_result_to_payload
from app.graph.models import GraphPayload, DocumentNodeModel, GraphNodeModel, GraphRelationshipModel
from app.graph.repository import MockNeo4jGraphStore, set_graph_repository, reset_graph_repository

c = TestClient(app)

def test_phase5_all():
    print("=" * 68)
    print("  PHASE 5 — NEO4J GRAPH DATABASE INTEGRATION AUTOMATED TEST SUITE")
    print("=" * 68)

    ts = int(time.time())
    uid_a = f"user-A-p5-{ts}"
    uid_b = f"user-B-p5-{ts}"
    proj_id = f"proj-cyber-p5-{ts}"
    src_id = f"src-cyber-p5-{ts}"

    # Use mock graph repository for isolated deterministic testing
    mock_repo = MockNeo4jGraphStore()
    set_graph_repository(mock_repo)

    # 1. Health Endpoints
    print("\n[Test 1] Health Endpoints:")
    res1 = c.get("/health")
    assert res1.status_code == 200, f"Health failed: {res1.text}"
    print("  [OK] System Health OK:", res1.json()["status"])

    res1_neo4j = c.get("/health/neo4j")
    assert res1_neo4j.status_code == 200, f"Neo4j health check failed: {res1_neo4j.text}"
    assert res1_neo4j.json()["ok"] is True
    print("  [OK] Neo4j Health Check:", res1_neo4j.json()["neo4j"])

    # 2. Auth Profile
    print("\n[Test 2] Auth Profile (User A):")
    res2 = c.get("/api/me", headers={"X-User-Uid": uid_a, "X-User-Email": "userA@example.com"})
    assert res2.status_code == 200
    print("  [OK] Auth Profile:", res2.json()["displayName"], f"({res2.json()['uid']})")

    # 3. Create Project
    print("\n[Test 3] Create Project (User A):")
    res3 = c.post(
        "/api/projects",
        headers={"X-User-Uid": uid_a},
        json={
            "id": proj_id,
            "name": "Cyber Threat Intelligence Report 2026",
            "description": "NTRO technical report covering APT ransomware campaigns and identity gateway vulnerabilities.",
        },
    )
    assert res3.status_code == 201
    print("  [OK] Created Project:", res3.json()["name"])

    # 4. Add Source Content
    print("\n[Test 4] Add Real Source Content:")
    sample_text = (
        "OpenAI developed GPT. "
        "GPT uses Transformer Architecture for model inference. "
        "Microsoft partnered with OpenAI on September 20, 2026 in San Francisco. "
        "The threat actor exploited CVE-2026-4418 in the Identity Gateway."
    )
    res4 = c.post(
        f"/api/projects/{proj_id}/sources",
        headers={"X-User-Uid": uid_a},
        json={
            "id": src_id,
            "name": "Cyber_Threat_Intelligence_Report_2026.pdf",
            "type": "PDF",
            "pages": 10,
            "size": "3.8 MB",
            "extractedText": sample_text,
        },
    )
    assert res4.status_code == 201
    print("  [OK] Added Source Document:", res4.json()["name"])

    # 5. Phase 3: AI Content Understanding
    print("\n[Test 5] Phase 3: Run AI Understanding:")
    res5 = c.post(
        f"/api/projects/{proj_id}/sources/{src_id}/analysis",
        headers={"X-User-Uid": uid_a},
        json={"forceRefresh": True},
    )
    assert res5.status_code == 200
    print("  [OK] AI Analysis completed.")

    # 6. Phase 4 -> Phase 5: DocLink to Graph Mapping & Ingestion
    print("\n[Test 6] Phase 4 -> Phase 5 Pipeline: DocLink to Neo4j Ingestion:")
    doclink_svc = DocLinkService()
    dl_result = doclink_svc.analyze_text(sample_text, document_id=src_id, document_name="Cyber_Threat_Intelligence_Report_2026.pdf")

    graph_svc = GraphService(repository=mock_repo)
    ingest_res = graph_svc.ingest_doclink_result(dl_result)

    assert ingest_res.ok is True
    assert ingest_res.document_id == src_id
    assert ingest_res.node_count > 0
    assert ingest_res.edge_count > 0
    print(f"  [OK] Ingested Graph Payload: {ingest_res.node_count} nodes, {ingest_res.edge_count} edges into Neo4j graph repository.")

    # 7. Document Node Verification (:Document)
    print("\n[Test 7] Verify Document Node Creation (:Document):")
    assert src_id in mock_repo.documents
    doc_node = mock_repo.documents[src_id]
    assert doc_node.filename == "Cyber_Threat_Intelligence_Report_2026.pdf"
    assert doc_node.file_type == "pdf"
    print(f"  [OK] Document Node verified: ({doc_node.filename}, ID: {doc_node.document_id})")

    # 8. Entity Node MERGE & Deduplication Verification (:Entity)
    print("\n[Test 8] Entity Node MERGE & Deduplication:")
    # Ingest duplicate payload with "OpenAI Inc." variant
    dl_result_dup = doclink_svc.analyze_text("OpenAI Inc. unveiled GPT.", document_id=src_id)
    graph_svc.ingest_doclink_result(dl_result_dup)

    openai_node = graph_svc.find_entity("OpenAI")
    assert openai_node is not None, "Entity OpenAI should exist in graph!"
    assert openai_node["canonical_name"] in ("OpenAI", "OpenAI Inc")
    print(f"  [OK] Entity MERGE verified: Canonical '{openai_node['canonical_name']}' (ID: {openai_node['entity_id']}).")

    # 9. Relationship Creation & Evidence Preservation (Source)-[RELATION]->(Target)
    print("\n[Test 9] Relationship Properties & Evidence Preservation:")
    openai_id = openai_node["entity_id"]
    rels = graph_svc.get_entity_relationships(openai_id)
    assert len(rels) > 0
    print(f"  [OK] Retrieved {len(rels)} relationships connected to entity '{openai_node['canonical_name']}':")
    for r in rels[:3]:
        print(f"    * ({r['source_id']}) -[:{r['relation_type']} {{confidence: {r['confidence']}, page: {r['page']}}}]-> ({r['target_id']})")
        if r.get("evidence_text"):
            print(f"      Evidence Quote: \"{r['evidence_text'][:55]}...\"")

    # 10. Graph Queries: Neighbors & Subgraph Retrieval
    print("\n[Test 10] Graph Neighbor & Subgraph Retrieval:")
    neighbors = graph_svc.get_neighbors(openai_id, depth=1)
    assert len(neighbors) > 0
    print(f"  [OK] Neighbors of '{openai_node['canonical_name']}': {[n['canonical_name'] for n in neighbors]}")

    doc_subgraph = graph_svc.get_document_graph(src_id)
    assert doc_subgraph.ok is True
    assert doc_subgraph.node_count > 0
    print(f"  [OK] Document Graph retrieved: {doc_subgraph.node_count} nodes, {doc_subgraph.edge_count} edges.")

    # 11. Graph Search API (GET /api/graph/search)
    print("\n[Test 11] Entity Substring Search API:")
    res11 = c.get("/api/graph/search?q=OpenAI", headers={"X-User-Uid": uid_a})
    assert res11.status_code == 200
    assert res11.json()["count"] > 0
    print(f"  [OK] Search returned {res11.json()['count']} entities matching query 'OpenAI'.")

    # 12. Graph Entity APIs (GET /api/graph/entity/{id} & relationships)
    print("\n[Test 12] Graph Entity API Endpoints:")
    res12_ent = c.get(f"/api/graph/entity/{openai_id}", headers={"X-User-Uid": uid_a})
    assert res12_ent.status_code == 200
    assert res12_ent.json()["ok"] is True

    res12_rels = c.get(f"/api/graph/entity/{openai_id}/relationships", headers={"X-User-Uid": uid_a})
    assert res12_rels.status_code == 200
    assert len(res12_rels.json()["relationships"]) > 0

    res12_neigh = c.get(f"/api/graph/entity/{openai_id}/neighbors", headers={"X-User-Uid": uid_a})
    assert res12_neigh.status_code == 200

    res12_doc = c.get(f"/api/graph/document/{src_id}", headers={"X-User-Uid": uid_a})
    assert res12_doc.status_code == 200

    print("  [OK] Graph Entity, Relationship, Neighbor, and Document API endpoints verified.")

    # 13. Graph Ingestion API (POST /api/graph/ingest)
    print("\n[Test 13] Graph Ingestion API Endpoint (POST /api/graph/ingest):")
    res13 = c.post(
        "/api/graph/ingest",
        headers={"X-User-Uid": uid_a},
        json={"document_id": src_id, "text": sample_text},
    )
    assert res13.status_code == 200
    assert res13.json()["ok"] is True
    print("  [OK] API Graph Ingestion successful.")

    # 14. Phase 5 UCKR Endpoints Regression Check
    print("\n[Test 14] Phase 5 UCKR Integration Endpoints:")
    res14_uckr = c.post(f"/api/projects/{proj_id}/sources/{src_id}/uckr", headers={"X-User-Uid": uid_a})
    assert res14_uckr.status_code == 201
    uckr_doc = res14_uckr.json()["uckr"]
    assert uckr_doc["version"] == 1
    assert uckr_doc["status"] == "valid"
    print(f"  [OK] Built UCKR Document Version {uckr_doc['version']} (ID: {uckr_doc['uckrId']}).")

    # 15. Clean up Project
    print("\n[Test 15] Clean up Project:")
    res15 = c.delete(f"/api/projects/{proj_id}", headers={"X-User-Uid": uid_a})
    assert res15.status_code == 200
    reset_graph_repository()
    print("  [OK] Cleaned up Test Project.")

    print("\n" + "=" * 68)
    print("  ALL 15 PHASE 5 NEO4J GRAPH INTEGRATION TESTS PASSED 100%!")
    print("=" * 68)
