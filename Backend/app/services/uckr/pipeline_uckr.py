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

from ...config.mongo import get_mongo_db
from ...utils.helpers import utcnow_iso
from ..sources import source_service

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
    # Normalize analysis object if nested under textAnalysis
    text_ana = analysis.get("textAnalysis", analysis) if isinstance(analysis, dict) else {}
    if not isinstance(text_ana, dict):
        text_ana = analysis

    pages = normalized.get("pages", []) or []
    page_of = {i + 1: p.get("text", "") for i, p in enumerate(pages)}
    doc_name = normalized.get("document", {}).get("name", "source")

    raw_facts = text_ana.get("facts") or analysis.get("facts", []) or []
    facts, citations = [], []
    for i, f in enumerate(raw_facts[:60]):
        if isinstance(f, dict):
            value = (f.get("text") or f.get("value") or "").strip()
            quote = (f.get("quote") or (f.get("source") or {}).get("quote") if isinstance(f.get("source"), dict) else None) or value
            src_loc = f.get("source") if isinstance(f.get("source"), dict) else {}
            page_no = int(src_loc.get("page") or f.get("page") or 0)
            conf = float(f.get("confidence", 0.95))
            fact_type = f.get("type") or _classify_fact(value, bool(re.search(r"\d", value)), bool(f.get("timestamp")))
        else:
            value = str(f).strip()
            quote = value
            page_no = 0
            conf = 0.9
            fact_type = "Proposition"

        if not value:
            continue

        if page_no == 0:
            for pn, ptext in page_of.items():
                if quote[:50] and quote[:50].lower() in ptext.lower():
                    page_no = pn
                    break

        fid = f"F-{i + 1:03d}"
        facts.append({
            "id": fid,
            "value": value,
            "type": fact_type,
            "sourceDoc": doc_name,
            "page": page_no or 1,
            "section": "",
            "confidence": round(conf, 3),
            "quote": quote,
            "usedInDeliverables": [],
        })
        citations.append({
            "id": f"C-{i + 1:03d}",
            "factId": fid,
            "quote": quote,
            "sourceDoc": doc_name,
            "page": page_no or 1,
        })

    raw_entities = text_ana.get("entities") or analysis.get("entities", []) or []
    entities = [
        {
            "id": f"E-{i + 1:03d}",
            "name": e.get("name", "") if isinstance(e, dict) else str(e),
            "category": (e.get("type") if isinstance(e, dict) else "Actor / Stakeholder") or "Actor / Stakeholder",
            "mentions": int(e.get("mentions", 1)) if isinstance(e, dict) else 1,
            "role": (e.get("role", "") if isinstance(e, dict) else ""),
        }
        for i, e in enumerate(raw_entities[:40])
    ]

    raw_events = text_ana.get("events") or analysis.get("events", []) or []
    events = [
        {
            "id": f"EV-{i + 1:03d}",
            "title": (e.get("event") or e.get("title", ""))[:200] if isinstance(e, dict) else str(e)[:200],
            "timestamp": str(e.get("date") or e.get("timestamp", "")) if isinstance(e, dict) else "",
            "impact": (e.get("impact", "") if isinstance(e, dict) else ""),
            "actors": (e.get("actors", []) if isinstance(e, dict) else []),
        }
        for i, e in enumerate(raw_events[:20])
    ]

    raw_metrics = text_ana.get("metrics") or analysis.get("metrics", []) or []
    metrics = [
        {
            "id": f"M-{i + 1:03d}",
            "name": (m.get("name") or m.get("context", "") or "Metric")[:120] if isinstance(m, dict) else "Metric",
            "value": str(m.get("value", "")) if isinstance(m, dict) else str(m),
            "unit": (m.get("unit", "") if isinstance(m, dict) else ""),
            "context": ((m.get("context", "") or "")[:300] if isinstance(m, dict) else ""),
            "confidence": float(m.get("confidence", 0.95)) if isinstance(m, dict) else 0.95,
        }
        for i, m in enumerate(raw_metrics[:30])
    ]

    raw_rels = text_ana.get("relationships") or analysis.get("relationships", []) or []
    relationships = [
        {
            "id": f"R-{i + 1:03d}",
            "source": r.get("source", "") if isinstance(r, dict) else "",
            "relation": r.get("relation", "related to") if isinstance(r, dict) else "related to",
            "target": r.get("target", "") if isinstance(r, dict) else "",
            "confidence": float(r.get("confidence", 0.8)) if isinstance(r, dict) else 0.8,
        }
        for i, r in enumerate(raw_rels[:30])
    ]

    raw_actions = text_ana.get("actions") or analysis.get("actions", []) or []
    actions = [
        {
            "id": f"A-{i + 1:03d}",
            "action": a.get("action", "") if isinstance(a, dict) else str(a),
            "priority": (a.get("priority", "P2 Medium") if isinstance(a, dict) else "P2 Medium"),
            "timeframe": (a.get("timeframe", "") if isinstance(a, dict) else ""),
            "owner": (a.get("owner", "") if isinstance(a, dict) else ""),
        }
        for i, a in enumerate(raw_actions[:20])
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
        "summary": text_ana.get("summary") or analysis.get("summary", ""),
        "provider": analysis.get("provider", "qwen2.5:7b"),
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
    from ..projects.project_service import get_project  # ownership of project

    get_project(project_id, uid)
    src = source_service.get_source(source_id, uid)
    if src.get("projectId") != project_id:
        raise HTTPException(status_code=400, detail="Source does not belong to this project.")
    norm = normalized or src.get("normalized") or {}
    uckr = build_uckr(norm, analysis, uid, project_id, source_id)
    saved = save_uckr(uckr)
    # cache analysis on the source for reuse
    get_mongo_db()["sources"].update_one(
        {"$or": [{"sourceId": source_id}, {"id": source_id}]},
        {"$set": {"analysis": {"provider": analysis.get("provider"), "textHash": analysis.get("textHash"),
                               "result": analysis, "cachedAt": utcnow_iso()}}},
    )
    return saved


def get_latest_uckr(project_id: str, uid: str, source_id: Optional[str] = None) -> dict:
    from ..projects.project_service import get_project

    get_project(project_id, uid)
    filt: dict[str, Any] = {"projectId": project_id, **_owner_filter(uid)}
    if source_id:
        filt["sourceId"] = source_id
    doc = get_mongo_db()["uckr"].find_one(filt, {"_id": 0}, sort=[("version", DESCENDING)])
    if doc:
        return doc

    # If not found, try to auto-build from existing analysis record or source
    db = get_mongo_db()
    ana_filt = {"projectId": project_id, **_owner_filter(uid)}
    if source_id:
        ana_filt["sourceId"] = source_id
    ana_doc = db["analysis"].find_one(ana_filt, {"_id": 0}, sort=[("updatedAt", DESCENDING)])
    
    src = None
    if source_id:
        try:
            src = source_service.get_source(source_id, uid)
        except Exception:
            pass
    if not src:
        src_doc = db["sources"].find_one({"projectId": project_id, **_owner_filter(uid)}, {"_id": 0})
        if src_doc:
            src = src_doc

    if ana_doc and src:
        sid = src.get("sourceId") or src.get("id") or "SRC_001"
        norm = src.get("normalized") or {}
        uckr = build_uckr(norm, ana_doc, uid, project_id, sid)
        return save_uckr(uckr)
    elif src:
        sid = src.get("sourceId") or src.get("id") or "SRC_001"
        from ..ai import analysis_service
        try:
            rec = analysis_service.analyze_source_sync(project_id, sid, uid)
            norm = src.get("normalized") or {}
            uckr = build_uckr(norm, rec.model_dump(), uid, project_id, sid)
            return save_uckr(uckr)
        except Exception as e:
            log.warning("Auto-analysis for UCKR failed: %s", e)

    raise HTTPException(status_code=404, detail="No UCKR found for this project yet.")


def list_uckrs(project_id: str, uid: str, limit: int = 20) -> list[dict]:
    from ..projects.project_service import get_project

    get_project(project_id, uid)
    cur = get_mongo_db()["uckr"].find(
        {"projectId": project_id, **_owner_filter(uid)}, {"_id": 0}
    ).sort("version", DESCENDING).limit(limit)
    return list(cur)


# --- legacy shim (kept for old imports) ---
def extract_uckr_from_text(text: str) -> dict:
    from ..ai.pipeline_orchestrator import analyze_text

    analysis = analyze_text(text or "")
    return build_uckr(
        {"pages": [{"pageNumber": 1, "text": text or ""}], "document": {"name": "inline-text"}},
        analysis, uid="legacy", project_id="legacy", source_id="legacy",
    )
