"""Consistency engine (Phase 6) — every deliverable is checked back against
the UCKR it was generated from. Nothing is hardcoded: all scores are
computed from text overlap between deliverable content and UCKR facts.

Persisted to MongoDB `validations`:
{projectId, uckrVersion, results{factPreservation, citationCoverage,
 unsupportedClaims, inconsistencies}, status: pass|warning|fail, checkedAt}
"""
from __future__ import annotations

import logging
import re
import uuid
from typing import Any

from fastapi import HTTPException
from pymongo import DESCENDING

from ..config.mongo import get_mongo_db
from ..utils.helpers import utcnow_iso

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
    """Compare one deliverable against UCKR facts. Returns per-type metrics."""
    facts = [f for f in (uckr.get("facts") or []) if f.get("value")]
    text = _flatten(content)
    text_words, text_nums = _words(text), set(_NUM.findall(text))

    preserved = 0
    cited = 0
    for f in facts[:20]:
        fw = _words(f["value"])
        if not fw:
            continue
        overlap = len(fw & text_words) / len(fw)
        if overlap >= 0.5:
            preserved += 1
        if f.get("quote", "")[:40] and f["quote"][:40] in text:
            cited += 1

    denom = max(1, min(len(facts), 20))
    fact_preservation = round(100 * preserved / denom, 1)
    citation_coverage = round(100 * cited / denom, 1)

    # numbers appearing in the deliverable but in no fact -> potential hallucinations
    fact_nums: set[str] = set()
    for f in facts:
        fact_nums |= set(_NUM.findall(f.get("value", "") + " " + f.get("quote", "")))
    inconsistencies = sorted(n for n in text_nums if n not in fact_nums)[:10]

    # sentences with no word overlap with any fact -> unsupported claims
    unsupported = 0
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 25]
    for s in sentences:
        sw = _words(s)
        if sw and not any(len(sw & _words(f["value"])) / max(1, len(sw)) >= 0.25 for f in facts[:20]):
            unsupported += 1

    return {"type": dtype, "factPreservation": fact_preservation,
            "citationCoverage": citation_coverage, "unsupportedClaims": unsupported,
            "inconsistencies": inconsistencies}


def validate_project(uid: str, project_id: str) -> dict:
    """Validate ALL deliverables of a project against its latest UCKR."""
    from .project_service import get_project

    get_project(project_id, uid)
    db = get_mongo_db()
    filt_owner = {"$or": [{"firebaseUid": uid}, {"userId": uid}]}
    uckr = db["uckr"].find_one({"projectId": project_id, **filt_owner}, sort=[("version", DESCENDING)])
    if not uckr:
        raise HTTPException(status_code=404, detail="No UCKR found — run analysis first.")
    deliverables = list(db["deliverables"].find(
        {"projectId": project_id, "uckrVersion": uckr.get("version"), **filt_owner}, {"_id": 0}))
    if not deliverables:
        raise HTTPException(status_code=404, detail="No deliverables for the current UCKR version.")

    per_type = [check_deliverable(uckr, d["type"], d["content"]) for d in deliverables]
    fact_pres = round(sum(p["factPreservation"] for p in per_type) / len(per_type), 1)
    cite_cov = round(sum(p["citationCoverage"] for p in per_type) / len(per_type), 1)
    unsupported = sum(p["unsupportedClaims"] for p in per_type)
    inconsist = [n for p in per_type for n in p["inconsistencies"]][:20]

    status = "pass" if (fact_pres >= 80 and unsupported == 0) else ("warning" if fact_pres >= 50 else "fail")
    now = utcnow_iso()
    doc = {
        "validationId": f"val-{uuid.uuid4().hex[:12]}",
        "firebaseUid": uid,
        "userId": uid,
        "projectId": project_id,
        "uckrVersion": uckr.get("version", 1),
        "results": {"factPreservation": fact_pres, "citationCoverage": cite_cov,
                    "unsupportedClaims": unsupported, "inconsistencies": inconsist,
                    "perType": per_type},
        "status": status,
        "checkedAt": now,
        "createdAt": now,
    }
    db["validations"].insert_one({**doc})
    doc.pop("_id", None)
    log.info("validation project=%s status=%s preservation=%s", project_id, status, fact_pres)
    return doc


def list_validations(uid: str, project_id: str, limit: int = 20) -> list[dict]:
    from .project_service import get_project

    get_project(project_id, uid)
    cur = get_mongo_db()["validations"].find(
        {"projectId": project_id, "$or": [{"firebaseUid": uid}, {"userId": uid}]}, {"_id": 0}
    ).sort("checkedAt", DESCENDING).limit(limit)
    return list(cur)


# --- legacy shim (kept for old route shape) ---
def validate_deliverable(deliverable_type: str, content: Any, source_text: str) -> dict:
    facts = [{"value": s, "quote": s}
             for s in re.split(r"(?<=[.!?])\s+", (source_text or "")) if len(s.strip()) > 20][:20]
    res = check_deliverable({"facts": facts}, deliverable_type, content or {})
    return {"valid": res["factPreservation"] >= 50 and res["unsupportedClaims"] == 0,
            "groundingScore": round(res["factPreservation"] / 100, 3),
            "issues": ([f"unsupported claims: {res['unsupportedClaims']}" ] if res["unsupportedClaims"] else [])
                      + ([f"unverifiable numbers: {res['inconsistencies'][:5]}"] if res["inconsistencies"] else []),
            "metrics": res}
