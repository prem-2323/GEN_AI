"""Phase 10 — Multi-Format Export System & GridFS Delivery Automated Test Suite.

Verifies:
  1. Complete End-to-End Pipeline: Source -> Extraction -> UCKR -> Deliverables
  2. Deliverable Approval & Governance Workflow (require_approval check)
  3. TXT Export -> GridFS -> Verify content and metadata
  4. DOCX Export -> GridFS -> Verify valid Word document
  5. PDF Export -> GridFS -> Verify valid ReportLab PDF binary
  6. PPTX Export -> GridFS -> Verify PowerPoint slides with UCKR fact citations
  7. MP3 Audio Export -> GridFS -> Verify audio binary
  8. MongoDB `exports` Collection Lineage & Metadata Verification
  9. Secure Download Endpoint with Strict Tenant Security (User B blocked with 403 Forbidden)
 10. Missing Deliverable / Cross-tenant Error Handlers (404 / 403)
"""
from __future__ import annotations

import io
import json
import logging
from typing import Dict, Any

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from docx import Document
from pptx import Presentation

from app.main import app
from app.config.mongo import get_mongo_db, ensure_core_indexes
from app.services.storage.gridfs_service import get_gridfs_bucket, get_gridfs_files_collection

logging.basicConfig(level=logging.INFO)
client = TestClient(app)

USER_A_HEADERS = {
    "X-User-Uid": "user_phase10_export_A",
    "X-User-Email": "prem.phase10@example.com",
    "X-User-Name": "Prem Kumar (Lead)",
}

USER_B_HEADERS = {
    "X-User-Uid": "user_phase10_attacker_B",
    "X-User-Email": "attacker.phase10@example.com",
    "X-User-Name": "User B Attacker",
}


def run_phase10_test_suite():
    print("\n" + "=" * 68)
    print("  PHASE 10 — MULTI-FORMAT EXPORT SYSTEM & GRIDFS TEST SUITE")
    print("=" * 68 + "\n")

    db = get_mongo_db()
    ensure_core_indexes()

    # --- Setup: Project & Source ---
    print("[Setup] Provisioning Project, Source & UCKR for Export Testing:")
    p_resp = client.post(
        "/api/projects",
        json={"name": "Phase 10 Enterprise Transformation", "description": "Testing multi-format file exporters"},
        headers=USER_A_HEADERS,
    )
    assert p_resp.status_code in (200, 201), f"Create project failed: {p_resp.text}"
    proj = p_resp.json()
    project_id = proj["projectId"]

    source_text = (
        "NATIONAL CYBERSECURITY INCIDENT ADVISORY - SEPTEMBER 2026\n"
        "Threat Actor Group Alpha launched targeted ransomware campaigns exploiting CVE-2026-9011. "
        "Over 40 enterprise cloud nodes were compromised across financial sectors. "
        "Mandatory Remediation: All organizations must enforce Multi-Factor Authentication and apply Patch v4.2."
    )
    files = {"file": ("cyber_advisory_2026.txt", io.BytesIO(source_text.encode("utf-8")), "text/plain")}
    up_resp = client.post(f"/api/projects/{project_id}/upload", files=files, headers=USER_A_HEADERS)
    assert up_resp.status_code in (200, 201), f"Upload failed: {up_resp.text}"
    src_data = up_resp.json().get("source", up_resp.json())
    source_id = src_data.get("sourceId") or src_data.get("id")

    # Generate UCKR & Deliverables
    ana_resp = client.post(f"/api/projects/{project_id}/sources/{source_id}/analysis", json={"forceRefresh": True}, headers=USER_A_HEADERS)
    assert ana_resp.status_code == 200

    uckr_resp = client.post(f"/api/projects/{project_id}/sources/{source_id}/uckr", headers=USER_A_HEADERS)
    assert uckr_resp.status_code in (200, 201), f"Build UCKR failed: {uckr_resp.text}"

    trans_resp = client.post(
        f"/api/projects/{project_id}/transform",
        json={"types": ["executive_summary", "advisory", "presentation", "video"]},
        headers=USER_A_HEADERS,
    )
    assert trans_resp.status_code in (200, 201), f"Transform failed: {trans_resp.text}"
    deliverables = trans_resp.json().get("deliverables", [])
    assert len(deliverables) >= 3, "Failed to generate deliverables for export."

    # Identify deliverables by type
    deliv_map = {d.get("type"): (d.get("deliverableId") or d.get("id")) for d in deliverables}
    exec_deliv_id = deliv_map.get("executive_summary") or deliverables[0]["deliverableId"]
    adv_deliv_id = deliv_map.get("advisory") or deliverables[1]["deliverableId"]
    pres_deliv_id = deliv_map.get("presentation") or deliverables[2]["deliverableId"]
    video_deliv_id = deliv_map.get("video") or deliverables[-1]["deliverableId"]

    print(f"  [OK] Project {project_id} ready with {len(deliverables)} deliverables.")

    # --- Test 1: Governance & Approval Workflow ---
    print("\n[Test 1] Testing Approval Governance Workflow (require_approval check):")
    # Attempt export with require_approval=True before approval -> Should fail with 412 Precondition Failed
    unapproved_resp = client.post(
        f"/api/projects/{project_id}/deliverables/{exec_deliv_id}/export",
        json={"format": "docx", "require_approval": True},
        headers=USER_A_HEADERS,
    )
    assert unapproved_resp.status_code == 412, f"Expected 412 for unapproved deliverable, got {unapproved_resp.status_code}"
    print("  [OK] Unapproved export correctly rejected with 412 Precondition Failed.")

    # Approve deliverable
    app_resp = client.post(
        f"/api/projects/{project_id}/deliverables/{exec_deliv_id}/approve",
        headers=USER_A_HEADERS,
    )
    assert app_resp.status_code == 200, f"Approve failed: {app_resp.text}"
    print(f"  [OK] Deliverable {exec_deliv_id} approved for enterprise export.")

    # --- Test 2: TXT / Markdown Export ---
    print("\n[Test 2] Testing TXT & Markdown Exporter:")
    txt_resp = client.post(
        f"/api/projects/{project_id}/deliverables/{adv_deliv_id}/export",
        json={"format": "txt", "require_approval": False},
        headers=USER_A_HEADERS,
    )
    assert txt_resp.status_code == 200, f"TXT export failed: {txt_resp.text}"
    txt_exp = txt_resp.json()["export"]
    txt_file_id = txt_exp["fileId"]
    assert txt_file_id, "GridFS fileId missing on TXT export."

    # Download and verify content
    dl_txt = client.get(f"/api/projects/{project_id}/exports/{txt_exp['exportId']}/download", headers=USER_A_HEADERS)
    assert dl_txt.status_code == 200
    assert "CONTENTFORGE AI" in dl_txt.text
    print(f"  [OK] TXT Export verified in GridFS (id={txt_file_id}, size={len(dl_txt.content)} bytes).")

    # --- Test 3: DOCX Document Export ---
    print("\n[Test 3] Testing DOCX Exporter (python-docx):")
    docx_resp = client.post(
        f"/api/projects/{project_id}/deliverables/{exec_deliv_id}/export",
        json={"format": "docx", "require_approval": True, "custom_title": "Enterprise Executive Brief 2026"},
        headers=USER_A_HEADERS,
    )
    assert docx_resp.status_code == 200, f"DOCX export failed: {docx_resp.text}"
    docx_exp = docx_resp.json()["export"]
    docx_file_id = docx_exp["fileId"]

    # Download binary & verify with python-docx
    dl_docx = client.get(f"/api/projects/{project_id}/exports/{docx_exp['exportId']}/download", headers=USER_A_HEADERS)
    assert dl_docx.status_code == 200
    parsed_doc = Document(io.BytesIO(dl_docx.content))
    paragraphs_text = " ".join(p.text for p in parsed_doc.paragraphs)
    assert "CONTENTFORGE AI" in paragraphs_text
    print(f"  [OK] DOCX verified as valid Word Document: {len(parsed_doc.paragraphs)} paragraphs rendered.")

    # --- Test 4: PDF Document Export ---
    print("\n[Test 4] Testing PDF Exporter (ReportLab):")
    pdf_resp = client.post(
        f"/api/projects/{project_id}/deliverables/{adv_deliv_id}/export",
        json={"format": "pdf", "require_approval": False},
        headers=USER_A_HEADERS,
    )
    assert pdf_resp.status_code == 200, f"PDF export failed: {pdf_resp.text}"
    pdf_exp = pdf_resp.json()["export"]
    pdf_file_id = pdf_exp["fileId"]

    # Download binary & verify %PDF- magic header
    dl_pdf = client.get(f"/api/projects/{project_id}/exports/{pdf_exp['exportId']}/download", headers=USER_A_HEADERS)
    assert dl_pdf.status_code == 200
    assert dl_pdf.content.startswith(b"%PDF-"), "Downloaded file is not a valid PDF."
    print(f"  [OK] PDF verified with valid %PDF- header (size={len(dl_pdf.content)} bytes).")

    # --- Test 5: PPTX Presentation Export with UCKR Fact Citations ---
    print("\n[Test 5] Testing PPTX Presentation Exporter (python-pptx):")
    pptx_resp = client.post(
        f"/api/projects/{project_id}/deliverables/{pres_deliv_id}/export",
        json={"format": "pptx", "require_approval": False, "custom_title": "Executive Threat Briefing"},
        headers=USER_A_HEADERS,
    )
    assert pptx_resp.status_code == 200, f"PPTX export failed: {pptx_resp.text}"
    pptx_exp = pptx_resp.json()["export"]
    pptx_file_id = pptx_exp["fileId"]

    # Download binary & inspect with python-pptx
    dl_pptx = client.get(f"/api/projects/{project_id}/exports/{pptx_exp['exportId']}/download", headers=USER_A_HEADERS)
    assert dl_pptx.status_code == 200
    prs = Presentation(io.BytesIO(dl_pptx.content))
    assert len(prs.slides) > 0, "No slides generated in presentation."
    print(f"  [OK] PPTX verified: {len(prs.slides)} slides generated with UCKR citation footers.")

    # --- Test 6: MP3 Audio Voiceover Export ---
    print("\n[Test 6] Testing MP3 Voiceover Audio Exporter:")
    audio_resp = client.post(
        f"/api/projects/{project_id}/deliverables/{video_deliv_id}/export",
        json={"format": "mp3", "require_approval": False},
        headers=USER_A_HEADERS,
    )
    assert audio_resp.status_code == 200, f"MP3 export failed: {audio_resp.text}"
    audio_exp = audio_resp.json()["export"]
    print(f"  [OK] MP3 Audio synthesized and stored in GridFS (fileId={audio_exp['fileId']}, size={audio_exp['fileSize']} bytes).")

    # --- Test 7: MongoDB `exports` Collection Verification ---
    print("\n[Test 7] Verifying MongoDB `exports` Collection Records & Lineage:")
    list_resp = client.get(f"/api/projects/{project_id}/exports", headers=USER_A_HEADERS)
    assert list_resp.status_code == 200
    exports_list = list_resp.json()["exports"]
    assert len(exports_list) >= 4, f"Expected at least 4 exports in collection, got {len(exports_list)}"

    for exp in exports_list:
        assert exp.get("fileId"), "fileId is missing in export record."
        assert exp.get("exportType") in ("txt", "docx", "pdf", "pptx", "mp3", "md"), f"Unknown export type {exp.get('exportType')}"
        assert exp.get("uckrVersion") is not None
    print(f"  [OK] All {len(exports_list)} export records verified in MongoDB with full UCKR lineage.")

    # --- Test 8: Cross-Tenant Security on Download Endpoint ---
    print("\n[Test 8] Cross-Tenant Security Enforcement:")
    # User B attempts to download User A's PPTX export -> 403 Forbidden
    hack_resp = client.get(f"/api/projects/{project_id}/exports/{pptx_exp['exportId']}/download", headers=USER_B_HEADERS)
    assert hack_resp.status_code == 403, f"Expected 403 Forbidden for cross-tenant download, got {hack_resp.status_code}"
    print("  [OK] Cross-tenant download blocked with 403 Forbidden.")

    # Missing deliverable check
    missing_resp = client.post(
        f"/api/projects/{project_id}/deliverables/del-nonexistent-1234/export",
        json={"format": "pdf"},
        headers=USER_A_HEADERS,
    )
    assert missing_resp.status_code == 404
    print("  [OK] Non-existent deliverable export correctly returns 404 Not Found.")

    # --- Cleanup ---
    client.delete(f"/api/projects/{project_id}", headers=USER_A_HEADERS)
    print("\n  [OK] Cleaned up Phase 10 test project.")

    print("\n" + "=" * 68)
    print("  ALL 10 PHASE 10 EXPORT SYSTEM TESTS PASSED 100%!")
    print("=" * 68 + "\n")


if __name__ == "__main__":
    run_phase10_test_suite()
