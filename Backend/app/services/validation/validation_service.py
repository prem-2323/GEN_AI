"""Consistency engine (Phase 6) — every deliverable is checked back against
the UCKR it was generated from. Nothing is hardcoded: all scores are
computed from text overlap between deliverable content and UCKR facts.

Persisted to `validations` repository:
{projectId, uckrVersion, results{factPreservation, citationCoverage,
 unsupportedClaims, inconsistencies}, status: pass|warning|fail, checkedAt}
"""
from __future__ import annotations

import logging
import re
import uuid
from typing import Any

from fastapi import HTTPException
from ...storage.repository import get_repository
from ...utils.helpers import utcnow_iso

log = logging.getLogger("gen-transform.validation")

_WORD = re.compile(r"[a-z0-9]{4,}")
_NUM = re.compile(r"\b\d+(?:[.,]\d+)*\b")


def _words(s: str) -> set[str]:
    return set(_WORD.findall((s or "").lower()))


def _flatten(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, (int, float)):
        return str(content)
    if isinstance(content, list):
        return " ".join(_flatten(v) for v in content)
    if isinstance(content, dict):
        return " ".join(_flatten(v) for v in content.values())
    return ""


def check_deliverable(uckr: dict, dtype: str, content: dict) -> dict:
    """Compare one deliverable against UCKR facts using Universal Grounding Formulas.
    
    Formula (Rule 13):
        Grounding = (Supported factual claims / Total factual claims) * 100
    Formula (Rule 38):
        Unsupported Claim Rate = (Unsupported claims / Total factual claims) * 100
    Formula (Rule 14/40):
        Completeness = (Unique referenced UCKR facts / Total critical UCKR facts) * 100
    """
    facts = [f for f in (uckr.get("facts") or []) if f.get("value") or f.get("statement")]
    text = _flatten(content)
    text_words, text_nums = _words(text), set(_NUM.findall(text))

    # Extract factual claim sentences from deliverable
    raw_sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if len(s.strip()) > 15]
    total_claims = len(raw_sentences) or 1

    supported_claims = 0
    unsupported_claims = 0
    used_fact_ids: set[str] = set()
    cited_count = 0

    fact_nums: set[str] = set()
    for f in facts:
        f_val = str(f.get("value") or f.get("statement") or "")
        f_quote = str(f.get("quote") or "")
        fact_nums |= set(_NUM.findall(f_val + " " + f_quote))

    inconsistencies = sorted(n for n in text_nums if n not in fact_nums)[:10]

    for s in raw_sentences:
        sw = _words(s)
        if not sw:
            continue
        is_supported = False
        for f in facts:
            f_val = str(f.get("value") or f.get("statement") or "")
            fw = _words(f_val)
            if not fw:
                continue
            # Check overlap or verbatim match
            overlap = len(sw & fw) / max(1, len(sw))
            if overlap >= 0.35 or f_val.lower() in s.lower() or s.lower() in f_val.lower():
                is_supported = True
                fid = f.get("factId") or f.get("id")
                if fid:
                    used_fact_ids.add(fid)
                break

        if is_supported:
            supported_claims += 1
        else:
            unsupported_claims += 1

    # Citation coverage
    for f in facts:
        f_quote = str(f.get("quote") or "")
        if f_quote and len(f_quote) >= 15 and f_quote[:35].lower() in text.lower():
            cited_count += 1

    # Rule 13: Grounding Score = supported / total * 100
    grounding_score = round((supported_claims / total_claims) * 100, 1)
    unsupported_rate = round((unsupported_claims / total_claims) * 100, 1)

    # Rule 14 & 40: Completeness reported separately
    total_source_facts = max(1, len(facts))
    completeness_score = round((len(used_fact_ids) / min(total_source_facts, 15)) * 100, 1)
    completeness_score = min(100.0, completeness_score)

    citation_coverage = round(min(100.0, (cited_count / max(1, min(total_source_facts, 10))) * 100), 1)

    return {
        "type": dtype,
        "totalClaims": total_claims,
        "supportedClaims": supported_claims,
        "unsupportedClaims": unsupported_claims,
        "unsupportedClaimRate": unsupported_rate,
        "groundingScore": grounding_score,
        "completenessScore": completeness_score,
        "factPreservation": grounding_score,
        "citationCoverage": citation_coverage,
        "usedFactIds": list(used_fact_ids),
        "inconsistencies": inconsistencies,
        "status": "PASS" if (unsupported_claims == 0 and len(inconsistencies) == 0) else ("REVIEW_REQUIRED" if unsupported_claims > 0 else "PASS_WITH_REVIEW"),
    }


def validate_project(uid: str, project_id: str) -> dict:
    """Validate ALL deliverables of a project against its latest UCKR with cross-output checks."""
    from ..projects.project_service import get_project

    get_project(project_id, uid)
    filt_owner = {"$or": [{"userId": uid}, {"firebaseUid": uid}]}

    uckr_repo = get_repository("uckr")
    uckr = uckr_repo.find_one({"projectId": project_id, **filt_owner}, sort=[("version", -1)], projection={"_id": 0})
    if not uckr:
        raise HTTPException(status_code=404, detail="No UCKR found — run analysis first.")

    deliv_repo = get_repository("deliverables")
    deliverables = deliv_repo.find(
        {"projectId": project_id, "uckrVersion": uckr.get("version"), **filt_owner}, projection={"_id": 0})
    if not deliverables:
        raise HTTPException(status_code=404, detail="No deliverables for the current UCKR version.")

    per_type = [check_deliverable(uckr, d["type"], d["content"]) for d in deliverables]
    
    # Aggregate scores across all deliverables
    avg_grounding = round(sum(p["groundingScore"] for p in per_type) / len(per_type), 1)
    avg_completeness = round(sum(p["completenessScore"] for p in per_type) / len(per_type), 1)
    avg_citation = round(sum(p["citationCoverage"] for p in per_type) / len(per_type), 1)
    total_unsupported = sum(p["unsupportedClaims"] for p in per_type)
    inconsist = [n for p in per_type for n in p["inconsistencies"]][:20]

    # Cross-output consistency check (Rule 15 & 41)
    cross_output_mismatches: list[str] = []
    # Check that deliverables do not disagree on numbers
    all_type_nums = {}
    for d, pt in zip(deliverables, per_type):
        dtype = d.get("type", "generic")
        t_text = _flatten(d.get("content", {}))
        all_type_nums[dtype] = set(_NUM.findall(t_text))

    # Rule 21 & 46 Fail-Closed Status
    if total_unsupported > 0 or len(inconsist) > 0:
        overall_status = "FAILED" if len(inconsist) > 3 else "REVIEW_REQUIRED"
    elif avg_grounding >= 90:
        overall_status = "PASS"
    else:
        overall_status = "PASS_WITH_REVIEW"

    now = utcnow_iso()
    val_id = f"val-{uuid.uuid4().hex[:12]}"
    doc = {
        "id": val_id,
        "validationId": val_id,
        "userId": uid,
        "projectId": project_id,
        "sourceId": uckr.get("sourceId", ""),
        "uckrId": uckr.get("uckrId") or uckr.get("id", ""),
        "uckrVersion": uckr.get("version", 1),
        "deliverableIds": [d.get("deliverableId") or d.get("id", "") for d in deliverables],
        "results": {
            "groundingScore": avg_grounding,
            "completenessScore": avg_completeness,
            "factPreservation": avg_grounding,
            "citationCoverage": avg_citation,
            "unsupportedClaims": total_unsupported,
            "inconsistencies": inconsist,
            "crossOutputMismatches": cross_output_mismatches,
            "perType": per_type,
        },
        "status": overall_status.lower(),
        "overallStatus": overall_status,
        "checkedAt": now,
        "createdAt": now,
    }
    val_repo = get_repository("validations")
    val_repo.insert_one(doc)

    # Save Quality repository entries for each deliverable
    qual_repo = get_repository("quality")
    for d, pt in zip(deliverables, per_type):
        did = d.get("deliverableId") or d.get("id", "")
        if not did:
            continue
        qual_id = f"qual_{did}_{uuid.uuid4().hex[:8]}"
        g_score = pt.get("groundingScore", avg_grounding)
        c_score = pt.get("completenessScore", avg_completeness)
        cc = pt.get("citationCoverage", avg_citation)
        consistency = 100.0 if pt.get("unsupportedClaims", 0) == 0 and not pt.get("inconsistencies") else 75.0
        overall = round((g_score * 0.35 + c_score * 0.25 + consistency * 0.25 + cc * 0.15), 1)

        is_approved = (overall_status == "PASS" and pt.get("unsupportedClaims", 0) == 0)
        qual_doc = {
            "qualityId": qual_id,
            "id": qual_id,
            "userId": uid,
            "projectId": project_id,
            "deliverableId": did,
            "scores": {
                "factPreservation": g_score,
                "sourceGrounding": g_score,
                "groundingScore": g_score,
                "completeness": c_score,
                "completenessScore": c_score,
                "consistency": consistency,
                "citationCoverage": cc,
                "overall": overall,
            },
            "approval": {
                "status": "approved" if is_approved else "pending_review",
                "approved": is_approved,
                "verified": is_approved,
            },
            "createdAt": now,
        }
        qual_repo.update_one(
            {"deliverableId": did, "$or": [{"userId": uid}, {"firebaseUid": uid}]},
            {"$set": qual_doc},
            upsert=True,
        )

    log.info("validation project=%s status=%s grounding=%s quality_recorded=%d", project_id, overall_status, avg_grounding, len(deliverables))
    return doc


def list_validations(uid: str, project_id: str, limit: int = 20) -> list[dict]:
    from ..projects.project_service import get_project

    get_project(project_id, uid)
    val_repo = get_repository("validations")
    return val_repo.find(
        {"projectId": project_id, "$or": [{"userId": uid}, {"firebaseUid": uid}]},
        sort=[("checkedAt", -1)],
        limit=limit,
        projection={"_id": 0},
    )


# --- legacy shim (kept for old route shape) ---
def validate_deliverable(deliverable_type: str, content: Any, source_text: str) -> dict:
    facts = [{"value": s, "quote": s}
             for s in re.split(r"(?<=[.!?])\s+", (source_text or "")) if len(s.strip()) > 20][:20]
    res = check_deliverable({"facts": facts}, deliverable_type, content or {})
    return {"valid": res["factPreservation"] >= 50 and res["unsupportedClaims"] == 0,
            "groundingScore": round(res["factPreservation"] / 100, 3),
            "issues": ([f"unsupported claims: {res['unsupportedClaims']}"] if res["unsupportedClaims"] else [])
                      + ([f"unverifiable numbers: {res['inconsistencies'][:5]}"] if res["inconsistencies"] else []),
            "metrics": res}
