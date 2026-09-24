import sys
from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)

print("=" * 65)
print("  PHASE 4 — REAL UCKR ENGINE END-TO-END AUTOMATED TEST SUITE")
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
print(f"    - Grounded Citations: {len(uckr1['citations'])}")
for ct in uckr1["citations"][:2]:
    print(f"      * [{ct['id']}] Page {ct['page']} | Chunk: {ct['chunkId']} | \"{ct['excerpt'][:50]}...\"")

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
print("  [OK] UCKR Validation Result:")
print(f"    - Status: {val['status']}")
print(f"    - Grounding Coverage: {val['groundingCoverage']}%")
print(f"    - Broken References: {len(val['brokenReferences'])}")
print(f"    - Missing Citations: {len(val['missingCitations'])}")
print(f"    - Duplicate IDs: {len(val['duplicateIds'])}")

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
print("\n[Test 10] Auditability Check: Fetch Historical Version 1:")
res10_v1 = c.get(
    f"/api/projects/{proj_id}/sources/{src_id}/uckr/1",
    headers={"X-User-Uid": uid_a},
)
assert res10_v1.status_code == 200
assert res10_v1.json()["uckr"]["version"] == 1
print("  [OK] Retrieved Historical Version 1 successfully.")

res10_v2 = c.get(
    f"/api/projects/{proj_id}/sources/{src_id}/uckr/2",
    headers={"X-User-Uid": uid_a},
)
assert res10_v2.status_code == 200
assert res10_v2.json()["uckr"]["version"] == 2
print("  [OK] Retrieved Version 2 successfully.")

# 11. Phase 4: Project-Level UCKR (UI View)
print("\n[Test 11] Project-Level UCKR Retrieval (Frontend Display):")
res11 = c.get(
    f"/api/projects/{proj_id}/uckr",
    headers={"X-User-Uid": uid_a},
)
assert res11.status_code == 200
assert res11.json()["uckr"]["version"] == 2
print("  [OK] Project-Level UCKR returns latest v2 with", len(res11.json()["uckr"]["facts"]), "facts.")

# 12. Security Multi-Tenant Isolation (User B)
print("\n[Test 12] Multi-Tenant Security Check (User B attempt to access User A UCKR):")
res12 = c.get(
    f"/api/projects/{proj_id}/sources/{src_id}/uckr",
    headers={"X-User-Uid": uid_b},
)
assert res12.status_code == 403, f"Expected 403, got {res12.status_code}"
print("  [OK] Cross-Tenant Access Blocked with 403 Forbidden.")

# 13. Cleanup
print("\n[Test 13] Clean up Project:")
res13 = c.delete(
    f"/api/projects/{proj_id}",
    headers={"X-User-Uid": uid_a},
)
assert res13.status_code == 200
print("  [OK] Cleaned up Test Project.")

print("\n" + "=" * 65)
print("  ALL 13 PHASE 4 UCKR ENGINE INTEGRATION TESTS PASSED 100%!")
print("=" * 65)
sys.exit(0)
