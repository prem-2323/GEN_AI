import sys
from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)

print("=" * 60)
print("  PHASE 3 & UCKR END-TO-END AUTOMATED TEST SUITE")
print("=" * 60)

uid_a = "user-A-test-uid"
uid_b = "user-B-test-uid"
proj_id = "proj-cyber-001"
src_id = "src-cyber-001"

# 1. Health
print("\n[Test 1] Health Endpoint:")
res1 = c.get("/health")
assert res1.status_code == 200, f"Health failed: {res1.text}"
print("  [OK] Health OK:", res1.json())

# 2. Auth /api/me
print("\n[Test 2] Auth Profile (User A):")
res2 = c.get("/api/me", headers={"X-User-Uid": uid_a, "X-User-Email": "userA@example.com"})
assert res2.status_code == 200, f"Auth failed: {res2.text}"
print("  [OK] Auth Profile:", res2.json()["displayName"], f"({res2.json()['uid']})")

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
assert res3.status_code == 201, f"Create project failed: {res3.text}"
print("  [OK] Created Project:", res3.json()["name"], f"(ID: {res3.json()['id']})")

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
assert res4.status_code == 201, f"Add source failed: {res4.text}"
print("  [OK] Added Source:", res4.json()["name"], f"({res4.json()['pages']} pages)")

# 5. Phase 3: Run AI Content Understanding (Qwen + Gemma)
print("\n[Test 5] Run AI Content Understanding (Qwen + Gemma):")
res5 = c.post(
    f"/api/projects/{proj_id}/sources/{src_id}/analysis",
    headers={"X-User-Uid": uid_a},
    json={"forceRefresh": True},
)
assert res5.status_code == 200, f"Analysis failed: {res5.text}"
ana = res5.json()
facts = ana["textAnalysis"]["facts"]
entities = ana["textAnalysis"]["entities"]
events = ana["textAnalysis"]["events"]
metrics = ana["textAnalysis"]["metrics"]
actions = ana["textAnalysis"]["actions"]

print(f"  [OK] Phase 3 Analysis Succeeded:")
print(f"    - Facts Extracted: {len(facts)}")
for f in facts[:2]:
    print(f"      * [{f['id']}] \"{f['text'][:70]}...\" (Confidence: {f['confidence']}, Page: {f.get('source', {}).get('page')})")
print(f"    - Entities Extracted: {len(entities)}")
for e in entities[:3]:
    print(f"      * [{e['id']}] {e['name']} ({e['type']})")
print(f"    - Metrics Extracted: {len(metrics)}")
for m in metrics[:3]:
    print(f"      * [{m['id']}] {m['value']} | context: \"{m['context'][:50]}...\"")
print(f"    - Actions Extracted: {len(actions)}")
for a in actions[:2]:
    print(f"      * [{a['id']}] {a['action']} (Priority: {a['priority']})")

# 6. Phase 3: Get Analysis Record
print("\n[Test 6] Fetch Saved Analysis Record:")
res6 = c.get(
    f"/api/projects/{proj_id}/sources/{src_id}/analysis",
    headers={"X-User-Uid": uid_a},
)
assert res6.status_code == 200
print("  [OK] Retrieved Analysis Record:", res6.json()["analysisId"], "| Status:", res6.json()["status"])

# 7. Phase 3: Analysis Status
print("\n[Test 7] Analysis Status Check:")
res7 = c.get(
    f"/api/projects/{proj_id}/sources/{src_id}/analysis/status",
    headers={"X-User-Uid": uid_a},
)
assert res7.status_code == 200
print("  [OK] Status Check:", res7.json())

# 8. Security Cross-Tenant Isolation
print("\n[Test 8] Security Cross-Tenant Check (User B attempting access to User A analysis):")
res8 = c.get(
    f"/api/projects/{proj_id}/sources/{src_id}/analysis",
    headers={"X-User-Uid": uid_b},
)
assert res8.status_code == 403, f"Expected 403, got {res8.status_code}"
print("  [OK] Cross-Tenant Access Correctly Blocked with 403 Forbidden")

# 9. Phase 4: Retrieve Project UCKR
print("\n[Test 9] Retrieve Project UCKR Knowledge Base:")
res9 = c.get(
    f"/api/projects/{proj_id}/uckr",
    headers={"X-User-Uid": uid_a},
)
assert res9.status_code == 200
print("  [OK] UCKR Retrieved Successfully")

# 10. Clean up test project
print("\n[Test 10] Clean up Project:")
res10 = c.delete(
    f"/api/projects/{proj_id}",
    headers={"X-User-Uid": uid_a},
)
assert res10.status_code == 200
print("  [OK] Deleted Test Project")

print("\n" + "=" * 60)
print("  ALL 10 PHASE 3 & UCKR INTEGRATION TESTS PASSED 100%!")
print("=" * 60)
sys.exit(0)
