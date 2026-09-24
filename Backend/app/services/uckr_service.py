"""UCKR engine (Phase 4) — the heart of the pipeline.

    Source -> (Qwen text + Gemma vision) -> UCKR Builder -> UCKR -> MongoDB `uckr`

Document:
{
  "_id": ..., "uckrId": "UCKR-...", "firebaseUid": ..., "userId": ...,
  "projectId": ..., "sourceId": ..., "version": 1,
  "facts": [{id, value, type, sourceDoc, page, section, confidence, quote, usedInDeliverables:[]}],
  "entities": [...], "events": [...], "metrics": [...],
  "relationships": [...], "actions": [...], "citations": [...],
  "stats": {...}, "createdAt": ..., "provider": ...
}
"""
from __future__ import annotations

import logging
import re
import uuid
from typing import Any, Optional

from fastapi import HTTPException
from pymongo import DESCENDING

from ..config.mongo import get_mongo_db
from ..utils.helpers import utcnow_iso
from . import source_service

log = logging.getLogger("gen-transform.uckr")

_FACT_TYPES = ("Metric", "Proposition", "Entity Finding", "Timeline / Event", "Action Mandate", "Risk / Impact")
_RISK_RE = re.compile(r"\b(risk|threat|vulnerab|attack|breach|critical|fail|loss|expos|malware|phishing)\b", re.I)


def _owner_filter(uid: str) -> dict:
    return {"$or": [{"firebaseUid": uid}, {"userId": uid}]}


def _classify_fact(value: str, has_number: bool, has_date: bool) -> str:
    if _RISK_RE.search(value):
        return "Risk / Impact"
    if has_number:
        return "Metric"
    if has_date:
        return "Timeline / Event"
    if re.match(r"^(must|should|shall|need to|ensure|implement|deploy|update|patch)\b", value.strip(), re.I):
        return "Action Mandate"
    return "Proposition"


def build_uckr(
    normalized: dict,
    analysis: dict,
    uid: str,
    project_id: str,
    source_id: str,
) -> dict:
    """Build a versioned UCKR from extraction + unified analysis (pure function)."""
    pages = normalized.get("pages", []) or []
    page_of = {i + 1: p.get("text", "") for i, p in enumerate(pages)}
    doc_name = normalized.get("document", {}).get("name", "source")

    facts, citations = [], []
    for i, f in enumerate(analysis.get("facts", [])[:60]):
        value = (f.get("value") or "").strip()
        quote = (f.get("quote") or value).strip()
        if not value:
            continue
        page_no = 0
        for pn, ptext in page_of.items():
            if quote[:60] and quote[:60] in ptext:
                page_no = pn
                break
        fid = f"F-{i + 1:03d}"
        facts.append({
            "id": fid,
            "value": value,
            "type": _classify_fact(value, bool(re.search(r"\d", value)), bool(f.get("timestamp"))),
            "sourceDoc": doc_name,
            "page": page_no,
            "section": "",
            "confidence": round(float(f.get("confidence", 0.8)), 3),
            "quote": quote,
            "usedInDeliverables": [],
        })
        citations.append({"id": f"C-{i + 1:03d}", "factId": fid, "quote": quote,
                          "sourceDoc": doc_name, "page": page_no})

    entities = [
        {"id": f"E-{i + 1:03d}", "name": e.get("name", ""), "category": "Actor / Stakeholder",
         "mentions": int(e.get("mentions", 1)), "role": e.get("role", "")}
        for i, e in enumerate(analysis.get("entities", [])[:40])
    ]
    events = [
        {"id": f"EV-{i + 1:03d}", "title": e.get("title", "")[:200],
         "timestamp": str(e.get("timestamp", "")), "impact": e.get("impact", ""),
         "actors": e.get("actors", [])}
        for i, e in enumerate(analysis.get("events", [])[:20])
    ]
    metrics = [
        {"id": f"M-{i + 1:03d}", "name": m.get("name", "")[:120], "value": str(m.get("value", "")),
         "unit": m.get("unit", ""), "context": (m.get("context", "") or "")[:300],
         "confidence": 0.8}
        for i, m in enumerate(analysis.get("metrics", [])[:30])
    ]
    relationships = [
        {"id": f"R-{i + 1:03d}", "source": r.get("source", ""), "relation": r.get("relation", "related to"),
         "target": r.get("target", ""), "confidence": 0.7}
        for i, r in enumerate(analysis.get("relationships", [])[:30])
    ]
    actions = [
        {"id": f"A-{i + 1:03d}", "action": a.get("action", "") if isinstance(a, dict) else str(a),
         "priority": (a.get("priority", "P2 Medium") if isinstance(a, dict) else "P2 Medium"),
         "timeframe": (a.get("timeframe", "") if isinstance(a, dict) else ""),
         "owner": (a.get("owner", "") if isinstance(a, dict) else "")}
        for i, a in enumerate(analysis.get("actions", [])[:20])
    ]

    total_facts = len(facts)
    coverage = round(100 * min(1.0, total_facts / 10), 1) if total_facts else 0.0
    return {
        "uckrId": f"UCKR-{uuid.uuid4().hex[:8].upper()}",
        "firebaseUid": uid,
        "userId": uid,
        "projectId": project_id,
        "sourceId": source_id,
        "stats": {
            "totalFacts": total_facts,
            "totalEntities": len(entities),
            "totalEvents": len(events),
            "totalMetrics": len(metrics),
            "totalActions": len(actions),
            "totalSources": 1,
            "totalRelationships": len(relationships),
            "coverage": coverage,
            "grounding": 100.0 if total_facts else 0.0,
            "readiness": round((coverage + (100.0 if total_facts else 0.0)) / 2, 1),
        },
        "facts": facts,
        "entities": entities,
        "events": events,
        "metrics": metrics,
        "relationships": relationships,
        "actions": actions,
        "citations": citations,
        "summary": analysis.get("summary", ""),
        "provider": analysis.get("provider", "unknown"),
        "createdAt": utcnow_iso(),
    }


def save_uckr(uckr: dict) -> dict:
    """Persist with auto-incremented version per (projectId, sourceId)."""
    col = get_mongo_db()["uckr"]
    latest = col.find_one(
        {"projectId": uckr["projectId"], "sourceId": uckr["sourceId"]},
        sort=[("version", DESCENDING)],
    )
    uckr["version"] = int((latest or {}).get("version", 0)) + 1
    uckr["updatedAt"] = utcnow_iso()
    col.insert_one({**uckr})
    uckr.pop("_id", None)
    log.info("UCKR saved project=%s source=%s version=%d facts=%d",
             uckr["projectId"], uckr["sourceId"], uckr["version"], len(uckr["facts"]))
    return uckr


def build_and_save(
    uid: str, project_id: str, source_id: str, analysis: dict, normalized: Optional[dict] = None
) -> dict:
    """Ownership-checked entry: loads source, builds UCKR, persists, caches analysis."""
    from .project_service import get_project  # ownership of project

    get_project(project_id, uid)
    src = source_service.get_source(source_id, uid)
    if src.get("projectId") != project_id:
        raise HTTPException(status_code=400, detail="Source does not belong to this project.")
    norm = normalized or src.get("normalized") or {}
    uckr = build_uckr(norm, analysis, uid, project_id, source_id)
    saved = save_uckr(uckr)
    # cache analysis on the source for reuse (Phase 12)
    get_mongo_db()["sources"].update_one(
        {"$or": [{"sourceId": source_id}, {"id": source_id}]},
        {"$set": {"analysis": {"provider": analysis.get("provider"), "textHash": analysis.get("textHash"),
                               "result": analysis, "cachedAt": utcnow_iso()}}},
    )
    return saved


def get_latest_uckr(project_id: str, uid: str, source_id: Optional[str] = None) -> dict:
    from .project_service import get_project

    get_project(project_id, uid)
    filt: dict[str, Any] = {"projectId": project_id, **_owner_filter(uid)}
    if source_id:
        filt["sourceId"] = source_id
    doc = get_mongo_db()["uckr"].find_one(filt, {"_id": 0}, sort=[("version", DESCENDING)])
    if not doc:
        raise HTTPException(status_code=404, detail="No UCKR found for this project yet.")
    return doc


def list_uckrs(project_id: str, uid: str, limit: int = 20) -> list[dict]:
    from .project_service import get_project

    get_project(project_id, uid)
    cur = get_mongo_db()["uckr"].find(
        {"projectId": project_id, **_owner_filter(uid)}, {"_id": 0}
    ).sort("version", DESCENDING).limit(limit)
    return list(cur)


# --- legacy shim (kept for old imports) ---
def extract_uckr_from_text(text: str) -> dict:
    from .ai_orchestrator import analyze_text

    analysis = analyze_text(text or "")
    return build_uckr(
        {"pages": [{"pageNumber": 1, "text": text or ""}], "document": {"name": "inline-text"}},
        analysis, uid="legacy", project_id="legacy", source_id="legacy",
    )
