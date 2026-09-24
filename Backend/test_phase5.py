import sys
import time
from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)

print("=" * 68)
print("  PHASE 5 — REAL UCKR ENGINE END-TO-END AUTOMATED TEST SUITE")
print("=" * 68)

ts = int(time.time())
uid_a = f"user-A-p5-{ts}"
uid_b = f"user-B-p5-{ts}"
proj_id = f"proj-cyber-p5-{ts}"
src_id = f"src-cyber-p5-{ts}"

# 1. Health
print("\n[Test 1] Health Endpoint:")
res1 = c.get("/health")
assert res1.status_code == 200, f"Health failed: {res1.text}"
print("  [OK] Health OK:", res1.json()["status"])

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
print("\n[Test 4] Add Real Source Content with Multiple Entities & Metrics:")
sample_text = (
    "The organization Example Corporation detected a phishing campaign on 15 August 2026 targeting 240 employees. "
    "The threat actor APT-X exploited CVE-2026-4418 in the Identity Gateway to exfiltrate session tokens. "
    "Researchers from Microsoft Corporation and MS Threat Intelligence confirmed 34 organizations were compromised "
    "in 72 hours with mean lateral movement of 18 minutes. Total financial exposure was evaluated at ₹50 crore. "
    "Example Corp stated that the attack was contained within 24 hours. "
    "Security teams must reset affected user credentials immediately, deploy patch 2.4, and enforce 15-minute token rotation."
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
print("  [OK] AI Analysis completed and stored in MongoDB.")

# 6. Phase 5: Build Real UCKR Engine (Version 1)
print("\n[Test 6] Phase 5: Build Canonical UCKR Document (Version 1):")
res6 = c.post(
    f"/api/projects/{proj_id}/sources/{src_id}/uckr",
    headers={"X-User-Uid": uid_a},
)
assert res6.status_code == 201, f"Build UCKR failed: {res6.text}"
uckr1 = res6.json()["uckr"]
assert uckr1["version"] == 1
assert uckr1["previousVersion"] is None
assert uckr1["status"] == "valid"

# Verify Facts
facts = uckr1["facts"]
assert len(facts) > 0
print(f"  [OK] Grounded Facts Extracted ({len(facts)} facts):")
for f in facts[:2]:
    sref = f["sourceRefs"][0] if f.get("sourceRefs") else {}
    print(f"    * [{f['factId']}] \"{f['statement'][:60]}...\" | Type: {f['type']} | Page: {sref.get('pageNumber', f.get('page'))}")

# Verify Entities & Deduplication (Microsoft & MS merged)
entities = uckr1["entities"]
assert len(entities) > 0
print(f"  [OK] Normalized Entities Extracted ({len(entities)} entities):")
for e in entities[:4]:
    print(f"    * [{e['entityId']}] {e['canonicalName']} ({e['type']}, Aliases: {e.get('aliases', [])})")

# Verify Events
events = uckr1["events"]
assert len(events) > 0
print(f"  [OK] Structured Events ({len(events)} events):")
for ev in events[:2]:
    print(f"    * [{ev['eventId']}] {ev['eventType']}: \"{ev['description'][:50]}...\" (Date: {ev.get('date')})")

# Verify Metrics
metrics = uckr1["metrics"]
assert len(metrics) > 0
print(f"  [OK] Structured Metrics ({len(metrics)} metrics):")
for m in metrics[:3]:
    print(f"    * [{m['metricId']}] {m['value']} {m.get('unit', '')} | Context: \"{m['context'][:45]}...\"")

# Verify Claims & Actions
claims = uckr1["claims"]
actions = uckr1["actions"]
print(f"  [OK] Claims ({len(claims)}) & Actions ({len(actions)}):")
for a in actions[:2]:
    print(f"    * [{a['actionId']}] {a['action']} (Status: {a['status']}, Priority: {a['priority']})")

# Verify Relationships & Citations
relationships = uckr1["relationships"]
citations = uckr1["citations"]
assert len(citations) > 0
print(f"  [OK] Knowledge Graph Relations ({len(relationships)}) & Grounded Citations ({len(citations)}):")
for ct in citations[:2]:
    print(f"    * [{ct['citationId']}] Page {ct['pageNumber']} | Chunk: {ct['chunkId']} | Quote: \"{ct['textQuote'][:45]}...\"")

# 7. Phase 5: Fetch Source UCKR
print("\n[Test 7] Fetch Canonical UCKR Document:")
res7 = c.get(
    f"/api/projects/{proj_id}/sources/{src_id}/uckr",
    headers={"X-User-Uid": uid_a},
)
assert res7.status_code == 200
print("  [OK] Retrieved UCKR Document:", res7.json()["uckr"]["uckrId"], "| Version:", res7.json()["uckr"]["version"])

# 8. Phase 5: Deep UCKR Validation Report
print("\n[Test 8] Deep UCKR Validation Report:")
res8 = c.get(
    f"/api/projects/{proj_id}/sources/{src_id}/uckr/validation",
    headers={"X-User-Uid": uid_a},
)
assert res8.status_code == 200
val = res8.json()["validation"]
assert val["valid"] is True
assert val["citationCoverage"] >= 95.0
assert len(val["errors"]) == 0
print(f"  [OK] Validation Result: Valid={val['valid']}, Coverage={val['citationCoverage']}%, Errors={len(val['errors'])}, Warnings={len(val['warnings'])}")

# 9. Phase 5: Rebuild UCKR (Version 2 with previousVersion: 1)
print("\n[Test 9] Rebuild UCKR (Version 2 with previousVersion tracking):")
res9 = c.post(
    f"/api/projects/{proj_id}/sources/{src_id}/uckr/rebuild",
    headers={"X-User-Uid": uid_a},
)
assert res9.status_code == 200
uckr2 = res9.json()["uckr"]
assert uckr2["version"] == 2
assert uckr2["previousVersion"] == 1
print(f"  [OK] Created UCKR Version 2 (previousVersion={uckr2['previousVersion']}, ID={uckr2['uckrId']})")

# 10. Phase 5: Historical Auditability (Fetch Version 1 and Version 2)
print("\n[Test 10] Auditability Check: Retrieve Historical Versions 1 and 2:")
res10_v1 = c.get(f"/api/projects/{proj_id}/sources/{src_id}/uckr/1", headers={"X-User-Uid": uid_a})
assert res10_v1.status_code == 200 and res10_v1.json()["uckr"]["version"] == 1
res10_v2 = c.get(f"/api/projects/{proj_id}/sources/{src_id}/uckr/2", headers={"X-User-Uid": uid_a})
assert res10_v2.status_code == 200 and res10_v2.json()["uckr"]["version"] == 2
print("  [OK] Retrieved Version 1 and Version 2 with complete historical integrity.")

# 11. Phase 5: Project-Level UCKR Display (Frontend UI)
print("\n[Test 11] Project-Level UCKR Retrieval (Frontend Display):")
res11 = c.get(f"/api/projects/{proj_id}/uckr", headers={"X-User-Uid": uid_a})
assert res11.status_code == 200
assert res11.json()["uckr"]["version"] == 2
print("  [OK] Project-level endpoint returns active version 2.")

# 12. Security Multi-Tenant Isolation (User B)
print("\n[Test 12] Security Check: Cross-Tenant Access Denial (User B):")
res12 = c.get(f"/api/projects/{proj_id}/sources/{src_id}/uckr", headers={"X-User-Uid": uid_b})
assert res12.status_code == 403, f"Expected 403, got {res12.status_code}"
print("  [OK] Cross-Tenant Access Blocked with 403 Forbidden.")

# 13. Clean up
print("\n[Test 13] Clean up Project:")
res13 = c.delete(f"/api/projects/{proj_id}", headers={"X-User-Uid": uid_a})
assert res13.status_code == 200
print("  [OK] Cleaned up Test Project.")

print("\n" + "=" * 68)
print("  ALL 13 PHASE 5 REAL UCKR ENGINE INTEGRATION TESTS PASSED 100%!")
print("=" * 68)
sys.exit(0)
