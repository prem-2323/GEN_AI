"""Phase 6 — Real Transformation Engine End-to-End Automated Test Suite.

Tests:
1. Health & Auth setup
2. Project creation (User A)
3. Source document registration
4. AI Analysis extraction
5. Canonical UCKR Builder (v1)
6. Real Transformation Engine generating all 7 deliverables:
   - linkedin
   - x (Twitter thread)
   - executive_summary
   - advisory
   - infographic specification
   - presentation slide deck
   - video script
7. Schema validity and Fact ID grounding verification
8. Output validator rejection of hallucinated / unknown fact IDs
9. List project deliverables endpoint
10. Get single deliverable by ID
11. Cross-tenant security isolation (User B access blocked)
12. Delete deliverable endpoint
13. Cleanup test project
"""
import os
import sys
import uuid
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.main import app

client = TestClient(app)

TEST_RUN_ID = str(uuid.uuid4().hex[:8])
USER_A_UID = f"user-A-p6-{TEST_RUN_ID}"
USER_B_UID = f"user-B-p6-{TEST_RUN_ID}"
PROJECT_ID = f"proj-cyber-p6-{TEST_RUN_ID}"
SOURCE_ID = f"src-cyber-p6-{TEST_RUN_ID}"

SAMPLE_DOC_TEXT = (
    "CYBER THREAT INTELLIGENCE REPORT 2026\n\n"
    "The organization Example Corporation detected a sophisticated phishing campaign on 15 August 2026 targeting 240 employees. "
    "The threat actor APT-X exploited CVE-2026-4418 in the Identity Gateway to access credential databases. "
    "Security operations teams successfully contained the breach within 24 hours with zero customer data loss. "
    "Must reset affected user credentials immediately, deploy patch 2.4.1 across all gateway clusters, and enable FIDO2 security keys."
)


def run_tests():
    print("====================================================================")
    print("  PHASE 6 — REAL TRANSFORMATION ENGINE END-TO-END AUTOMATED TEST SUITE")
    print("====================================================================\n")

    # 1. Health
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print(f"[Test 1] Health Endpoint:\n  [OK] Health OK: {res.json().get('status')}\n")

    # 2. Auth Profile User A
    res = client.get("/api/me", headers={"X-User-Uid": USER_A_UID, "X-User-Email": "usera@example.com"})
    assert res.status_code == 200, f"Auth failed: {res.text}"
    print(f"[Test 2] Auth Profile (User A):\n  [OK] Auth Profile: {res.json().get('email')}\n")

    # 3. Create Project
    res = client.post(
        "/api/projects",
        headers={"X-User-Uid": USER_A_UID},
        json={
            "id": PROJECT_ID,
            "name": "Phase 6 Cyber Threat Intelligence Project",
            "description": "Validation of UCKR transformation engine across all 7 deliverable formats.",
            "status": "created",
        },
    )
    assert res.status_code == 201, f"Create project failed: {res.text}"
    print(f"[Test 3] Create Project (User A):\n  [OK] Created Project ID: {PROJECT_ID}\n")

    # 4. Create Source
    res = client.post(
        f"/api/projects/{PROJECT_ID}/sources",
        headers={"X-User-Uid": USER_A_UID},
        json={
            "id": SOURCE_ID,
            "filename": "Cyber_Threat_Intelligence_Report_2026.pdf",
            "extractedText": SAMPLE_DOC_TEXT,
            "status": "ready",
            "pages": 4,
            "chunks": [
                {
                    "chunkId": "chunk_001",
                    "pageNumber": 1,
                    "text": SAMPLE_DOC_TEXT,
                }
            ],
        },
    )
    assert res.status_code == 201, f"Add source failed: {res.text}"
    print(f"[Test 4] Add Real Source Document:\n  [OK] Added Source: {SOURCE_ID}\n")

    # 5. Run AI Analysis
    res = client.post(
        f"/api/projects/{PROJECT_ID}/sources/{SOURCE_ID}/analysis",
        headers={"X-User-Uid": USER_A_UID},
        json={"mode": "deterministic"},
    )
    assert res.status_code == 200, f"Analysis failed: {res.text}"
    print(f"[Test 5] AI Content Analysis:\n  [OK] Structured analysis completed.\n")

    # 6. Build Canonical UCKR (Phase 5)
    res = client.post(
        f"/api/projects/{PROJECT_ID}/sources/{SOURCE_ID}/uckr",
        headers={"X-User-Uid": USER_A_UID},
    )
    assert res.status_code == 201, f"UCKR build failed: {res.text}"
    uckr_data = res.json().get("uckr", {})
    valid_fact_ids = [f["factId"] for f in uckr_data.get("facts", [])]
    print(f"[Test 6] Canonical UCKR Knowledge Base (v{uckr_data.get('version')}):")
    print(f"  [OK] Total Facts: {len(uckr_data.get('facts', []))} ({valid_fact_ids})")
    print(f"  [OK] Total Entities: {len(uckr_data.get('entities', []))}")
    print(f"  [OK] Total Metrics: {len(uckr_data.get('metrics', []))}\n")

    # 7. Real Transformation Engine — Generate All 7 Deliverables
    target_types = [
        "linkedin",
        "x",
        "executive_summary",
        "advisory",
        "infographic",
        "presentation",
        "video_script",
    ]
    res = client.post(
        f"/api/projects/{PROJECT_ID}/transform",
        headers={"X-User-Uid": USER_A_UID},
        json={
            "sourceId": SOURCE_ID,
            "uckrVersion": 1,
            "outputTypes": target_types,
            "configuration": {
                "audience": "executive",
                "tone": "professional",
                "language": "English",
                "detailLevel": "medium",
                "objective": "awareness",
            },
        },
    )
    assert res.status_code == 201, f"Transform failed: {res.text}"
    trans_res = res.json()
    assert trans_res.get("ok") is True
    deliverables = trans_res.get("deliverables", [])
    assert len(deliverables) == 7, f"Expected 7 deliverables, got {len(deliverables)}"

    print("[Test 7] Transformed UCKR into 7 Communication Deliverables:")
    deliv_ids = {}
    for d in deliverables:
        dtype = d.get("type")
        did = d.get("id") or d.get("_id")
        deliv_ids[dtype] = did
        status = d.get("status")
        used_facts = d.get("usedFactIds", [])
        print(f"  * [{dtype.upper()}] ID: {did} | Status: {status} | Used Facts: {used_facts}")
        # Verify fact grounding
        for fid in used_facts:
            assert fid in valid_fact_ids, f"Deliverable {dtype} used unknown fact ID {fid} not in UCKR!"
    print()

    # 8. Test Output Validator: Rejects Unknown Fact IDs
    from app.services.transformation.output_validator import validate_deliverable_output
    invalid_content = {
        "title": "Alert",
        "body": "Fake content",
        "usedFactIds": ["fact_001", "fact_999_fake"],
        "hashtags": ["#Alert"],
    }
    is_valid, errors, warnings, _ = validate_deliverable_output("linkedin", invalid_content, uckr_data)
    assert is_valid is False, "Output validator failed to reject invalid fact ID!"
    assert any("fact_999_fake" in err for err in errors)
    print(f"[Test 8] Output Validator Rejection Test:\n  [OK] Successfully rejected invalid fact_999_fake with errors: {errors}\n")

    # 9. List Deliverables for Project
    res = client.get(
        f"/api/projects/{PROJECT_ID}/deliverables",
        headers={"X-User-Uid": USER_A_UID},
    )
    assert res.status_code == 200, f"List deliverables failed: {res.text}"
    listed = res.json().get("deliverables", [])
    assert len(listed) >= 7, f"Expected >= 7 listed deliverables, got {len(listed)}"
    print(f"[Test 9] List Project Deliverables Endpoint:\n  [OK] Found {len(listed)} deliverables in MongoDB `deliverables` collection.\n")

    # 10. Get Single Deliverable by ID
    first_deliv_id = deliverables[0]["id"]
    res = client.get(
        f"/api/projects/{PROJECT_ID}/deliverables/{first_deliv_id}",
        headers={"X-User-Uid": USER_A_UID},
    )
    assert res.status_code == 200, f"Get deliverable failed: {res.text}"
    single_doc = res.json().get("deliverable", {})
    assert single_doc.get("_id") == first_deliv_id or single_doc.get("id") == first_deliv_id
    assert single_doc.get("uckrVersion") == 1
    assert "content" in single_doc
    print(f"[Test 10] Get Single Deliverable ({single_doc.get('type')}):\n  [OK] Deliverable ID: {first_deliv_id} (UCKR v{single_doc.get('uckrVersion')})\n")

    # 11. Security Check: Cross-Tenant Access Blocked for User B
    res = client.get(
        f"/api/projects/{PROJECT_ID}/deliverables",
        headers={"X-User-Uid": USER_B_UID},
    )
    assert res.status_code in (403, 404), f"Expected 403/404 for User B, got {res.status_code}"
    print(f"[Test 11] Security Check: Cross-Tenant Access Denial (User B):\n  [OK] Blocked unauthorized access with HTTP {res.status_code}.\n")

    # 12. Delete Single Deliverable
    res = client.delete(
        f"/api/projects/{PROJECT_ID}/deliverables/{first_deliv_id}",
        headers={"X-User-Uid": USER_A_UID},
    )
    assert res.status_code == 200, f"Delete deliverable failed: {res.text}"
    print(f"[Test 12] Delete Deliverable Endpoint:\n  [OK] Deleted deliverable {first_deliv_id}.\n")

    # 13. Cleanup Project
    res = client.delete(
        f"/api/projects/{PROJECT_ID}",
        headers={"X-User-Uid": USER_A_UID},
    )
    assert res.status_code == 200, f"Delete project failed: {res.text}"
    print(f"[Test 13] Clean up Project:\n  [OK] Deleted test project {PROJECT_ID}.\n")

    print("====================================================================")
    print("  ALL 13 PHASE 6 REAL TRANSFORMATION ENGINE INTEGRATION TESTS PASSED 100%!")
    print("====================================================================")


if __name__ == "__main__":
    run_tests()
