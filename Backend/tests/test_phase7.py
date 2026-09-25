"""Phase 7 — Real Consistency Engine End-to-End Automated Test Suite.

Tests:
1. Health & Auth setup
2. Project creation (User A)
3. Source document registration
4. AI Analysis extraction
5. Canonical UCKR Builder (v1)
6. Deliverable Generation (LinkedIn, X, Executive Summary, Advisory)
7. Phase 7 Consistency Validation (Baseline: All Consistent -> PASS)
8. Contradiction Detection (Number Mismatch: 240 -> 420)
9. Contradiction Detection (Date Mismatch: 15 August -> 16 August with ISO normalization)
10. Unsupported Claim Detection (Ungrounded financial figure: ₹5 crore)
11. Individual Deliverable Validation Endpoint
12. Error-Feedback Regeneration Flow (Regenerate -> Contradictions Resolved -> PASS)
13. Get Latest Validation Audit Report
14. Security Check: Cross-Tenant Denial (User B blocked)
15. Clean up test project
"""
import os
import sys
import uuid
from fastapi.testclient import TestClient

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.main import app
from app.config.mongo import get_mongo_db

client = TestClient(app)

TEST_RUN_ID = str(uuid.uuid4().hex[:8])
USER_A_UID = f"user-A-p7-{TEST_RUN_ID}"
USER_B_UID = f"user-B-p7-{TEST_RUN_ID}"
PROJECT_ID = f"proj-cyber-p7-{TEST_RUN_ID}"
SOURCE_ID = f"src-cyber-p7-{TEST_RUN_ID}"

SAMPLE_DOC_TEXT = (
    "CYBER THREAT INTELLIGENCE REPORT 2026\n\n"
    "The organization Example Corporation detected a sophisticated phishing campaign on 15 August 2026 targeting 240 employees. "
    "The threat actor APT-X exploited CVE-2026-4418 in the Identity Gateway to access credential databases. "
    "Security operations teams successfully contained the breach within 24 hours with zero customer data loss. "
    "Must reset affected user credentials immediately, deploy patch 2.4.1 across all gateway clusters, and enable FIDO2 security keys."
)


def run_tests():
    print("====================================================================")
    print("  PHASE 7 — REAL CONSISTENCY ENGINE END-TO-END AUTOMATED TEST SUITE")
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
            "name": "Phase 7 Consistency Engine Verification",
            "description": "Validation of factual grounding, contradictions, unsupported claims, and scores.",
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
    print(f"[Test 6] Canonical UCKR Knowledge Base (v{uckr_data.get('version')}):")
    print(f"  [OK] Facts: {len(uckr_data.get('facts', []))} | Entities: {len(uckr_data.get('entities', []))} | Metrics: {len(uckr_data.get('metrics', []))}\n")

    # 7. Generate Deliverables (Phase 6)
    target_types = ["linkedin", "x", "executive_summary", "advisory"]
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
    deliverables = res.json().get("deliverables", [])
    assert len(deliverables) == 4
    deliv_map = {d["type"]: d["id"] for d in deliverables}
    print(f"[Test 7] Generated Deliverables:\n  [OK] Deliverables: {deliv_map}\n")

    # 8. Phase 7 Baseline Validation (Should PASS with high scores)
    res = client.post(
        f"/api/projects/{PROJECT_ID}/sources/{SOURCE_ID}/validate",
        headers={"X-User-Uid": USER_A_UID},
        json={"uckrVersion": 1},
    )
    assert res.status_code == 200, f"Validate failed: {res.text}"
    val_report = res.json()
    scores = val_report.get("scores", {})
    print(f"[Test 8] Baseline Consistency Validation Report:")
    print(f"  [OK] Consistency Score: {scores.get('consistency')}%")
    print(f"  [OK] Fact Preservation: {scores.get('factPreservation')}%")
    print(f"  [OK] Citation Coverage: {scores.get('citationCoverage')}%")
    print(f"  [OK] Unsupported Claims: {scores.get('unsupportedClaims')}")
    print(f"  [OK] Overall Status: {val_report.get('overallStatus')}\n")
    assert val_report.get("overallStatus") in ("PASS", "WARNING")
    assert scores.get("consistency", 0) >= 80.0

    # 9. Contradiction Detection — Number Mismatch (240 -> 420)
    db = get_mongo_db()
    advisory_id = deliv_map["advisory"]
    # Corrupt advisory in DB to introduce 420 number mismatch
    if db is not None:
        db.deliverables.update_one(
            {"_id": advisory_id},
            {"$set": {"content.observations": ["The campaign targeted 420 employees in the finance department."]}}
        )

    res = client.post(
        f"/api/projects/{PROJECT_ID}/deliverables/{advisory_id}/validate",
        headers={"X-User-Uid": USER_A_UID},
    )
    assert res.status_code == 200
    adv_check = res.json().get("result", {})
    checks = adv_check.get("checks", [])
    num_contradictions = [c for c in checks if c.get("status") == "contradiction" and c.get("category") == "metric"]
    assert len(num_contradictions) > 0, "Failed to detect numerical contradiction (240 vs 420)!"
    print(f"[Test 9] Numerical Contradiction Detection Test:")
    print(f"  [OK] Detected Contradiction: Expected {num_contradictions[0].get('expected')} but found {num_contradictions[0].get('found')}\n")

    # 10. Contradiction Detection — Date Mismatch (15 August -> 16 August)
    if db is not None:
        db.deliverables.update_one(
            {"_id": advisory_id},
            {"$set": {"content.observations": ["Incident occurred on 16 August 2026 affecting systems."]}}
        )

    res = client.post(
        f"/api/projects/{PROJECT_ID}/deliverables/{advisory_id}/validate",
        headers={"X-User-Uid": USER_A_UID},
    )
    assert res.status_code == 200
    adv_check = res.json().get("result", {})
    checks = adv_check.get("checks", [])
    date_contradictions = [c for c in checks if c.get("status") == "contradiction" and c.get("category") == "date"]
    assert len(date_contradictions) > 0, "Failed to detect date contradiction (2026-08-15 vs 2026-08-16)!"
    print(f"[Test 10] Date Contradiction Detection Test:")
    print(f"  [OK] Detected Date Contradiction: Expected {date_contradictions[0].get('expected')} but found {date_contradictions[0].get('found')}\n")

    # 11. Unsupported Claim Detection — Ungrounded Currency Figure (₹5 crore)
    linkedin_id = deliv_map["linkedin"]
    if db is not None:
        db.deliverables.update_one(
            {"_id": linkedin_id},
            {"$set": {"content.body": "The phishing campaign caused ₹5 crore in financial losses across operations."}}
        )

    res = client.post(
        f"/api/projects/{PROJECT_ID}/deliverables/{linkedin_id}/validate",
        headers={"X-User-Uid": USER_A_UID},
    )
    assert res.status_code == 200
    li_check = res.json().get("result", {})
    unsupported = li_check.get("unsupportedClaims", [])
    assert len(unsupported) > 0, "Failed to detect unsupported financial figure (₹5 crore)!"
    print(f"[Test 11] Unsupported Claim Detection Test:")
    print(f"  [OK] Detected Unsupported Claim: {unsupported[0]}\n")

    # 12. Error-Feedback Regeneration Flow
    # Regenerate advisory to fix corrupted state and re-validate
    res = client.post(
        f"/api/projects/{PROJECT_ID}/deliverables/{advisory_id}/regenerate",
        headers={"X-User-Uid": USER_A_UID},
        json={
            "validationFeedback": [
                "Ensure date is 15 August 2026",
                "Ensure affected count is 240 employees",
            ]
        },
    )
    assert res.status_code == 200, f"Regenerate failed: {res.text}"
    regen_res = res.json()
    assert regen_res.get("ok") is True
    val_after_regen = regen_res.get("validation", {})
    assert val_after_regen.get("status") in ("PASS", "WARNING"), f"Regenerated status: {val_after_regen.get('status')}"
    print(f"[Test 12] Error-Feedback Regeneration Flow:")
    print(f"  [OK] Deliverable {advisory_id} regenerated and revalidated with status: {val_after_regen.get('status')}\n")

    # 13. Get Latest Validation Report
    res = client.get(
        f"/api/projects/{PROJECT_ID}/sources/{SOURCE_ID}/validation",
        headers={"X-User-Uid": USER_A_UID},
    )
    assert res.status_code == 200, f"Get validation failed: {res.text}"
    assert "scores" in res.json()
    print(f"[Test 13] Get Latest Validation Audit Report:\n  [OK] Retrieved validation ID: {res.json().get('id')}\n")

    # 14. Security Check: Cross-Tenant Access Denial (User B)
    res = client.post(
        f"/api/projects/{PROJECT_ID}/sources/{SOURCE_ID}/validate",
        headers={"X-User-Uid": USER_B_UID},
        json={"uckrVersion": 1},
    )
    assert res.status_code == 403, f"Expected 403 Forbidden for User B, got {res.status_code}"
    print(f"[Test 14] Security Check: Cross-Tenant Access Denial (User B):\n  [OK] Blocked unauthorized access with HTTP 403.\n")

    # 15. Clean up Project
    res = client.delete(
        f"/api/projects/{PROJECT_ID}",
        headers={"X-User-Uid": USER_A_UID},
    )
    assert res.status_code == 200, f"Delete project failed: {res.text}"
    print(f"[Test 15] Clean up Project:\n  [OK] Cleaned up Test Project {PROJECT_ID}.\n")

    print("====================================================================")
    print("  ALL 15 PHASE 7 REAL CONSISTENCY ENGINE INTEGRATION TESTS PASSED 100%!")
    print("====================================================================")


if __name__ == "__main__":
    run_tests()
