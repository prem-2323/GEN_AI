import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.doclink.service import DocLinkService
from app.doclink.schemas import RawEntity, RawFact, RawRelation, EntityType, RelationType
from app.doclink.validator import validate_raw_entities, validate_raw_facts, validate_raw_relations

c = TestClient(app)

print("=" * 65)
print("  PHASE 4 — DOCLINK & UCKR ENGINE END-TO-END AUTOMATED TEST SUITE")
print("=" * 65)

uid_a = "user-A-phase4-uid"
uid_b = "user-B-phase4-uid"
proj_id = "proj-cyber-p4-001"
src_id = "src-cyber-p4-001"

# 1. Health
print("\n[Test 1] Health Endpoint:")
res1 = c.get("/health")
assert res1.status_code == 200, f"Health failed: {res1.text}"
print("  [OK] Health OK:", res1.json())

# 2. Auth Profile
print("\n[Test 2] Auth Profile (User A):")
res2 = c.get("/api/me", headers={"X-User-Uid": uid_a, "X-User-Email": "userA@example.com"})
assert res2.status_code == 200
print("  [OK] Auth Profile:", res2.json()["displayName"], f"({res2.json()['uid']})")

# Clean up any leftover project state from prior runs
c.delete(f"/api/projects/{proj_id}", headers={"X-User-Uid": uid_a})

# 3. Create Project
print("\n[Test 3] Create Project (User A):")
res3 = c.post(
    "/api/projects",
    headers={"X-User-Uid": uid_a},
    json={
        "id": proj_id,
        "name": "Cyber Threat Intelligence Report",
        "description": "Analysis of ransomware campaigns and identity gateway CVE-2026-4418 vulnerabilities.",
    },
)
assert res3.status_code == 201
print("  [OK] Created Project:", res3.json()["name"])

# 4. Add Source Content
print("\n[Test 4] Add Source Content to Project:")
sample_text = (
    "Organization X detected a ransomware campaign on 15 August 2026 affecting 25 systems. "
    "The attack exploited CVE-2026-4418 in the Identity Gateway. 34 organizations were compromised "
    "in 72 hours with mean lateral movement of 18 minutes. CVSS score was evaluated at 9.9. "
    "Security teams must deploy patch 2.4 immediately and enforce 15-minute token rotation."
)
res4 = c.post(
    f"/api/projects/{proj_id}/sources",
    headers={"X-User-Uid": uid_a},
    json={
        "id": src_id,
        "name": "Cyber_Threat_Intelligence_Report.pdf",
        "type": "PDF",
        "pages": 14,
        "size": "4.2 MB",
        "extractedText": sample_text,
    },
)
assert res4.status_code == 201
print("  [OK] Added Source:", res4.json()["name"])

# 5. Phase 3: Run AI Content Understanding
print("\n[Test 5] Phase 3: Run AI Content Understanding (Qwen + Gemma):")
res5 = c.post(
    f"/api/projects/{proj_id}/sources/{src_id}/analysis",
    headers={"X-User-Uid": uid_a},
    json={"forceRefresh": True},
)
assert res5.status_code == 200
print("  [OK] AI Analysis completed and stored in MongoDB analysis collection.")

# 6. Phase 4: Build Real UCKR Knowledge Base
print("\n[Test 6] Phase 4: Build Real UCKR Knowledge Base:")
res6 = c.post(
    f"/api/projects/{proj_id}/sources/{src_id}/uckr",
    headers={"X-User-Uid": uid_a},
)
assert res6.status_code == 201, f"Build UCKR failed: {res6.text}"
uckr1 = res6.json()["uckr"]
assert uckr1["version"] == 1
assert uckr1["status"] == "valid"
assert len(uckr1["facts"]) > 0
assert len(uckr1["entities"]) > 0
assert len(uckr1["citations"]) > 0
print(f"  [OK] UCKR Built Successfully:")
print(f"    - UCKR ID: {uckr1['uckrId']} (Version: {uckr1['version']}, Status: {uckr1['status']})")
print(f"    - Grounded Facts: {len(uckr1['facts'])}")
for f in uckr1["facts"][:2]:
    print(f"      * [{f['id']}] \"{f['value'][:65]}...\" (Page: {f['page']}, Citations: {f['sourceRefs']})")
print(f"    - Normalized Entities: {len(uckr1['entities'])}")
for e in uckr1["entities"][:3]:
    print(f"      * [{e['id']}] {e['canonicalName']} ({e['type']}, Aliases: {e.get('aliases', [])})")

# 7. Phase 4: Get Source UCKR
print("\n[Test 7] Fetch Source UCKR:")
res7 = c.get(
    f"/api/projects/{proj_id}/sources/{src_id}/uckr",
    headers={"X-User-Uid": uid_a},
)
assert res7.status_code == 200
print("  [OK] Retrieved Source UCKR:", res7.json()["uckr"]["uckrId"])

# 8. Phase 4: Deep UCKR Validation
print("\n[Test 8] Deep UCKR Validation Report:")
res8 = c.get(
    f"/api/projects/{proj_id}/sources/{src_id}/uckr/validation",
    headers={"X-User-Uid": uid_a},
)
assert res8.status_code == 200
val = res8.json()["validation"]
assert val["status"] == "valid"
print(f"  [OK] UCKR Validation Status: {val['status']} (Grounding Coverage: {val['groundingCoverage']}%)")

# 9. Phase 4: Rebuild UCKR (Creates Version 2)
print("\n[Test 9] Rebuild UCKR (Versioning Test -> Creates v2):")
res9 = c.post(
    f"/api/projects/{proj_id}/sources/{src_id}/uckr/rebuild",
    headers={"X-User-Uid": uid_a},
)
assert res9.status_code == 200
uckr2 = res9.json()["uckr"]
assert uckr2["version"] == 2
print(f"  [OK] Rebuilt UCKR with Version: {uckr2['version']} (UCKR ID: {uckr2['uckrId']})")

# 10. Phase 4: Retrieve Historical Version 1 and Version 2
print("\n[Test 10] Auditability Check: Fetch Historical Version 1 & Version 2:")
res10_v1 = c.get(
    f"/api/projects/{proj_id}/sources/{src_id}/uckr/1",
    headers={"X-User-Uid": uid_a},
)
assert res10_v1.status_code == 200
assert res10_v1.json()["uckr"]["version"] == 1

res10_v2 = c.get(
    f"/api/projects/{proj_id}/sources/{src_id}/uckr/2",
    headers={"X-User-Uid": uid_a},
)
assert res10_v2.status_code == 200
assert res10_v2.json()["uckr"]["version"] == 2
print("  [OK] Retrieved Historical Version 1 & 2 successfully.")

# 11. Multi-Tenant Security Check
print("\n[Test 11] Multi-Tenant Security Check (User B attempt to access User A UCKR):")
res11 = c.get(
    f"/api/projects/{proj_id}/sources/{src_id}/uckr",
    headers={"X-User-Uid": uid_b},
)
assert res11.status_code == 403
print("  [OK] Cross-Tenant Access Blocked with 403 Forbidden.")

# =========================================================================
# DOCLINK ENGINE TESTS (Phase 4 Specification)
# =========================================================================

# 12. DocLink API — Direct Text Analysis (POST /api/doclink/analyze-text)
print("\n[Test 12] DocLink Engine Direct Text Analysis API (POST /api/doclink/analyze-text):")
doclink_sample = (
    "OpenAI announced a new AI model in San Francisco on September 20, 2026. "
    "Microsoft partnered with OpenAI. The company uses PyTorch for model training."
)
res12 = c.post(
    "/api/doclink/analyze-text",
    headers={"X-User-Uid": uid_a},
    json={"text": doclink_sample, "document_id": "doc_test_001"},
)
assert res12.status_code == 200, f"DocLink analyze-text failed: {res12.text}"
dl_resp = res12.json()
assert dl_resp["status"] == "completed"
assert len(dl_resp["entities"]) >= 3
assert len(dl_resp["facts"]) >= 1
assert len(dl_resp["relations"]) >= 1

# Verify Entity Extraction types
entity_types = {e["type"] for e in dl_resp["entities"]}
entity_names = {e["canonical_name"] for e in dl_resp["entities"]}
assert "ORGANIZATION" in entity_types
assert "LOCATION" in entity_types or "San Francisco" in entity_names
assert "DATE" in entity_types or "September 20, 2026" in entity_names
assert "TECHNOLOGY" in entity_types or "PyTorch" in entity_names

# Verify Evidence / Source Tracking
for ent in dl_resp["entities"]:
    assert "evidence" in ent
    assert len(ent["evidence"]) > 0, f"Entity {ent['canonical_name']} missing evidence tracking!"
    assert ent["evidence"][0]["document_id"] == "doc_test_001"

print(f"  [OK] DocLink Extracted {len(dl_resp['entities'])} entities, {len(dl_resp['facts'])} facts, {len(dl_resp['relations'])} relations.")
print(f"    - Extracted Entity Types: {entity_types}")

# 13. DocLink Graph-Ready Structure (Nodes + Edges, persisted=False)
print("\n[Test 13] DocLink Graph-Ready Structure Verification:")
graph = dl_resp.get("graph")
assert graph is not None
assert len(graph["nodes"]) > 0
assert len(graph["edges"]) > 0
assert graph["persisted"] is False, "Neo4j persistence should NOT be executed in Phase 4!"
print(f"  [OK] Graph-Ready Structure generated: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges (persisted=False).")

# 14. DocLink Normalization & Deduplication
print("\n[Test 14] DocLink Entity Normalization & Deduplication:")
service = DocLinkService()
dup_text = "OpenAI announced Model X. Open AI later confirmed the release. OpenAI Inc. deployed it."
res14 = service.analyze_text(dup_text, document_id="doc_dup_001")
ents14 = res14.entities
openai_cluster = [e for e in ents14 if "openai" in e.canonical_name.lower()]
assert len(openai_cluster) == 1, f"Expected 1 merged OpenAI entity, got {len(openai_cluster)}"
merged_ent = openai_cluster[0]
assert merged_ent.canonical_name == "OpenAI" or "OpenAI" in merged_ent.surface_forms
print(f"  [OK] Successfully merged 'OpenAI', 'Open AI', 'OpenAI Inc.' into canonical entity '{merged_ent.canonical_name}'.")

# 15. DocLink Validator Rejection Tests
print("\n[Test 15] DocLink Validator Rejection of Invalid Data:")
bad_raw_entities = [
    {"text": "a", "type": "ORGANIZATION"}, # Name too short
    {"text": "InvalidEntity", "type": "NON_EXISTENT_TYPE"}, # Invalid type
    {"text": "Microsoft", "type": "ORGANIZATION"}, # Valid entity
]
accepted_e, rejected_e = validate_raw_entities(bad_raw_entities)
assert len(accepted_e) == 1
assert accepted_e[0].text == "Microsoft"
assert len(rejected_e) == 2

bad_raw_relations = [
    {"source": "OpenAI", "relation": "DEVELOPED", "target": "OpenAI"}, # Self-relation
    {"source": "", "relation": "DEVELOPED", "target": "GPT"}, # Missing source
    {"source": "Microsoft", "relation": "PARTNERED_WITH", "target": "OpenAI"}, # Valid
]
accepted_r, warn_r, rejected_r = validate_raw_relations(bad_raw_relations)
assert len(accepted_r) == 1
assert accepted_r[0].source == "Microsoft" and accepted_r[0].target == "OpenAI"
assert len(rejected_r) == 2

print("  [OK] Validator cleanly rejected invalid entity names, invalid types, self-relations, and missing endpoints.")

# 16. DocLink Document Analysis Endpoint (POST /api/doclink/analyze & GET /api/doclink/{doc_id})
print("\n[Test 16] DocLink Document Analysis API Endpoints:")
res16_post = c.post(
    "/api/doclink/analyze",
    headers={"X-User-Uid": uid_a},
    json={"document_id": src_id, "projectId": proj_id},
)
assert res16_post.status_code == 200, f"DocLink analyze failed: {res16_post.text}"
assert res16_post.json()["status"] == "completed"

res16_get = c.get(
    f"/api/doclink/{src_id}",
    headers={"X-User-Uid": uid_a},
)
assert res16_get.status_code == 200
assert res16_get.json()["document_id"] == src_id
print("  [OK] DocLink Document API endpoints (POST & GET) working as expected.")

# 17. Clean up
print("\n[Test 17] Clean up Test Project:")
res17 = c.delete(
    f"/api/projects/{proj_id}",
    headers={"X-User-Uid": uid_a},
)
assert res17.status_code == 200
print("  [OK] Cleaned up Test Project.")

print("\n" + "=" * 65)
print("  ALL 17 PHASE 4 DOCLINK & UCKR INTEGRATION TESTS PASSED 100%!")
print("=" * 65)
sys.exit(0)
