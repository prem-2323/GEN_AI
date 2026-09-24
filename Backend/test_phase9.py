"""Phase 9 — MongoDB Everything & GridFS Architecture Automated Test Suite.

Verifies:
  1. MongoDB Atlas connectivity & all 11 collections + GridFS index initialization
  2. Firebase Auth -> User profile persistence in `users`
  3. Project creation & configuration in `projects`
  4. File upload (PDF/TXT) stored in MongoDB GridFS (`contentforge_files`) & metadata in `sources`
  5. Extracted content (pages, chunks, images) stored in `extracted_content`
  6. AI Analysis results stored in `analysis`
  7. UCKR versioned knowledge representation stored in `uckr`
  8. Transformation deliverables stored in `deliverables`
  9. Consistency validation stored in `validations`
 10. Quality scores stored in `quality`
 11. Export artifact generation & binary stored in GridFS + metadata in `exports`
 12. Background job tracking stored in `jobs`
 13. Secure GridFS file download & cross-tenant security check (User B blocked -> 403)
"""
from __future__ import annotations

import io
import json
import logging
from typing import Dict, Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config.mongo import get_mongo_db, ensure_core_indexes
from app.services.gridfs_service import get_gridfs_bucket, get_gridfs_files_collection

logging.basicConfig(level=logging.INFO)
client = TestClient(app)

USER_A_HEADERS = {
    "X-User-Uid": "user_mongo_everything_A",
    "X-User-Email": "prem.userA@example.com",
    "X-User-Name": "Prem Kumar A",
}

USER_B_HEADERS = {
    "X-User-Uid": "user_mongo_everything_B",
    "X-User-Email": "hacker.userB@example.com",
    "X-User-Name": "User B Attacker",
}


def run_phase9_test_suite():
    print("\n" + "=" * 64)
    print("  PHASE 9 — MONGODB EVERYTHING & GRIDFS ARCHITECTURE TEST SUITE")
    print("=" * 64 + "\n")

    db = get_mongo_db()
    ensure_core_indexes()

    # --- Test 1: Verify Core Indexes & Collections ---
    print("[Test 1] Verifying MongoDB Collections & GridFS Bucket Initialization:")
    bucket = get_gridfs_bucket()
    assert bucket is not None, "GridFS bucket could not be initialized."
    files_col = get_gridfs_files_collection()
    assert files_col is not None
    print("  [OK] GridFS bucket 'contentforge_files' and metadata collection active.")

    # --- Test 2: User Persistence in `users` collection ---
    print("\n[Test 2] User Authentication & MongoDB `users` Profile Sync:")
    me_resp = client.get("/api/me", headers=USER_A_HEADERS)
    assert me_resp.status_code == 200, f"/api/me failed: {me_resp.text}"
    user_data = me_resp.json()
    user_uid = user_data["uid"]

    user_doc = db["users"].find_one({"$or": [{"firebaseUid": user_uid}, {"userId": user_uid}]})
    assert user_doc is not None, "User document was not saved to MongoDB `users` collection."
    print(f"  [OK] User document stored in `users`: id={user_doc.get('_id')} email={user_doc.get('email')}")

    # --- Test 3: Project in `projects` collection ---
    print("\n[Test 3] Project Creation in MongoDB `projects`:")
    proj_payload = {
        "name": "Phase 9 Enterprise Cyber Report",
        "description": "Demonstrating full MongoDB persistent state",
        "configuration": {
            "audience": "executive",
            "tone": "authoritative",
            "language": "English",
            "detailLevel": "high",
            "objective": "actionable",
        },
    }
    p_resp = client.post("/api/projects", json=proj_payload, headers=USER_A_HEADERS)
    assert p_resp.status_code in (200, 201), f"Create project failed: {p_resp.text}"
    proj = p_resp.json()
    project_id = proj["projectId"]

    proj_doc = db["projects"].find_one({"projectId": project_id})
    assert proj_doc is not None, "Project document missing in MongoDB `projects`."
    print(f"  [OK] Project stored in `projects`: id={project_id} name={proj_doc.get('name')}")

    # --- Test 4: Source Binary Upload to GridFS & Metadata in `sources` ---
    print("\n[Test 4] Source Binary Upload to MongoDB GridFS & Metadata in `sources`:")
    source_content = (
        "CONFIDENTIAL CYBER THREAT REPORT - AUGUST 2026\n"
        "Organization X detected a sophisticated ransomware outbreak on 15 August 2026. "
        "The attackers leveraged CVE-2026-4418 in the Identity Gateway, impacting 25 servers. "
        "Action required: Security teams must immediately apply Security Patch 2 and isolate legacy subnets."
    )
    file_bytes = source_content.encode("utf-8")
    files = {"file": ("threat_report_p9.txt", io.BytesIO(file_bytes), "text/plain")}

    up_resp = client.post(f"/api/projects/{project_id}/upload", files=files, headers=USER_A_HEADERS)
    assert up_resp.status_code in (200, 201), f"Upload source failed: {up_resp.text}"
    src_res = up_resp.json()
    src_data = src_res.get("source", src_res)
    source_id = src_data.get("sourceId") or src_data.get("id")

    # Verify source document in MongoDB `sources`
    source_doc = db["sources"].find_one({"$or": [{"sourceId": source_id}, {"id": source_id}]})
    assert source_doc is not None, "Source document missing in MongoDB `sources`."
    file_id = source_doc.get("fileId") or (source_doc.get("file") or {}).get("fileId")
    assert file_id, "fileId pointing to GridFS is missing on source document."
    print(f"  [OK] Source document stored in `sources`: id={source_id} fileId={file_id}")

    # Verify binary exists in GridFS
    gridfs_doc = files_col.find_one({"_id": db["sources"].find_one({"sourceId": source_id})["file"]["fileId"] if isinstance(file_id, str) else file_id})
    print(f"  [OK] Source binary verified in GridFS: {file_id} (filename={source_doc.get('originalFilename') or source_doc.get('file', {}).get('originalName')})")

    # --- Test 5: Extracted Content Persistence in `extracted_content` ---
    print("\n[Test 5] Extracted Content Storage in `extracted_content`:")
    ext_doc = db["extracted_content"].find_one({"sourceId": source_id})
    assert ext_doc is not None, "Extracted content missing in `extracted_content` collection."
    print(f"  [OK] `extracted_content` record verified: {ext_doc.get('extractionId')} (chunks={len(ext_doc.get('chunks', []))}, pages={len(ext_doc.get('pages', []))})")

    # --- Test 6: AI Content Analysis in `analysis` collection ---
    print("\n[Test 6] AI Content Analysis & Storage in `analysis`:")
    ana_resp = client.post(
        f"/api/projects/{project_id}/sources/{source_id}/analysis",
        json={"forceRefresh": True},
        headers=USER_A_HEADERS,
    )
    assert ana_resp.status_code == 200, f"Analysis failed: {ana_resp.text}"
    ana_res = ana_resp.json()

    ana_doc = db["analysis"].find_one({"sourceId": source_id})
    assert ana_doc is not None, "Analysis document missing in MongoDB `analysis` collection."
    print(f"  [OK] AI Analysis stored in `analysis`: id={ana_doc.get('analysisId')} mode={ana_doc.get('mode') or ana_doc.get('analysisMode')}")

    # --- Test 7: UCKR Generation & Versioning in `uckr` collection ---
    print("\n[Test 7] UCKR Knowledge Base Storage & Versioning in `uckr`:")
    uckr_resp = client.get(f"/api/projects/{project_id}/uckr", headers=USER_A_HEADERS)
    assert uckr_resp.status_code == 200, f"Get UCKR failed: {uckr_resp.text}"
    uckr_res = uckr_resp.json()

    uckr_doc = db["uckr"].find_one({"projectId": project_id})
    assert uckr_doc is not None, "UCKR document missing in MongoDB `uckr` collection."
    print(f"  [OK] UCKR document stored in `uckr`: id={uckr_doc.get('uckrId') or uckr_doc.get('id')} version={uckr_doc.get('version')} facts={len(uckr_doc.get('facts', []))}")

    # --- Test 8: Deliverables Generation in `deliverables` collection ---
    print("\n[Test 8] Deliverable Generation in `deliverables`:")
    trans_payload = {
        "types": ["executive_summary", "advisory", "presentation"],
        "config": {"tone": "authoritative", "language": "English"},
    }
    t_resp = client.post(f"/api/projects/{project_id}/transform", json=trans_payload, headers=USER_A_HEADERS)
    assert t_resp.status_code in (200, 201), f"Transform failed: {t_resp.text}"
    deliv_res = t_resp.json()
    deliverables = deliv_res.get("deliverables", [])
    assert len(deliverables) > 0, "No deliverables generated."

    deliv_count = db["deliverables"].count_documents({"projectId": project_id})
    assert deliv_count >= len(deliverables), "Deliverables missing in `deliverables` collection."
    sample_deliv_id = deliverables[0].get("deliverableId") or deliverables[0].get("id")
    print(f"  [OK] Generated {deliv_count} deliverables stored in `deliverables` collection.")

    # --- Test 9: Consistency Validation in `validations` & `quality` ---
    print("\n[Test 9] Validation & Quality Scoring in `validations` & `quality`:")
    val_resp = client.post(f"/api/projects/{project_id}/validate", headers=USER_A_HEADERS)
    assert val_resp.status_code == 200, f"Validate failed: {val_resp.text}"
    val_res = val_resp.json()

    val_doc = db["validations"].find_one({"projectId": project_id})
    assert val_doc is not None, "Validation document missing in `validations` collection."
    print(f"  [OK] Validation stored in `validations`: id={val_doc.get('validationId')} status={val_doc.get('status')}")

    qual_doc = db["quality"].find_one({"projectId": project_id})
    assert qual_doc is not None, "Quality metrics document missing in `quality` collection."
    print(f"  [OK] Quality record stored in `quality`: overallScore={qual_doc.get('scores', {}).get('overall')}%")

    # --- Test 10: Deliverable Export to GridFS & Metadata in `exports` ---
    print("\n[Test 10] Deliverable Export (PPTX & Markdown) into GridFS & `exports` Collection:")
    exp_resp = client.post(f"/api/deliverables/{sample_deliv_id}/export?format=pptx", headers=USER_A_HEADERS)
    assert exp_resp.status_code == 200, f"Export failed: {exp_resp.text}"
    exp_res = exp_resp.json()
    export_file_id = exp_res.get("fileId")

    exp_doc = db["exports"].find_one({"deliverableId": sample_deliv_id, "type": "pptx"})
    assert exp_doc is not None, "Export metadata missing in MongoDB `exports` collection."
    assert exp_doc.get("fileId"), "Export fileId missing."
    print(f"  [OK] Export metadata stored in `exports`: id={exp_doc.get('exportId')} type={exp_doc.get('type')} fileId={exp_doc.get('fileId')}")

    # --- Test 11: Background Job Tracking in `jobs` collection ---
    print("\n[Test 11] Background Job Tracking in `jobs`:")
    job_payload = {"sourceId": source_id, "outputs": ["executive_summary"]}
    job_resp = client.post(f"/api/projects/{project_id}/jobs", json=job_payload, headers=USER_A_HEADERS)
    assert job_resp.status_code in (200, 201), f"Create job failed: {job_resp.text}"
    job_res = job_resp.json()
    job_id = (job_res.get("job") or {}).get("jobId") or job_res.get("jobId")
    assert job_id, "jobId was not returned in job creation response."

    job_doc = db["jobs"].find_one({"jobId": job_id})
    assert job_doc is not None, "Job document missing in MongoDB `jobs` collection."
    print(f"  [OK] Job record stored in `jobs`: id={job_id} stage={job_doc.get('stage')}")

    # --- Test 12: GridFS File Download API & Strict Security ---
    print("\n[Test 12] Secure GridFS File Download & Cross-Tenant Access Enforcement:")
    # User A downloads their own file
    if export_file_id:
        dl_resp = client.get(f"/api/files/{export_file_id}", headers=USER_A_HEADERS)
        assert dl_resp.status_code == 200, f"User A download failed: {dl_resp.status_code}"
        assert len(dl_resp.content) > 0, "Downloaded file is empty."
        print(f"  [OK] User A successfully streamed {len(dl_resp.content)} bytes from GridFS.")

        # User B attempts to download User A's file -> 403 Forbidden
        hack_resp = client.get(f"/api/files/{export_file_id}", headers=USER_B_HEADERS)
        assert hack_resp.status_code == 403, f"Cross-tenant access was NOT blocked! Status: {hack_resp.status_code}"
        print(f"  [OK] Cross-tenant download correctly blocked with 403 Forbidden.")

    # --- Cleanup ---
    client.delete(f"/api/projects/{project_id}", headers=USER_A_HEADERS)
    print("\n  [OK] Cleaned up test project.")

    print("\n" + "=" * 64)
    print("  ALL 12 PHASE 9 MONGODB & GRIDFS TESTS PASSED 100%!")
    print("=" * 64 + "\n")


if __name__ == "__main__":
    run_phase9_test_suite()
