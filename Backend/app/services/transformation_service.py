"""Transformation engine (Phase 5) — outputs are generated FROM the UCKR,
never independently from the raw document.

Types: linkedin, twitter (X), advisory, executive_summary, infographic,
       presentation, video
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

from fastapi import HTTPException
from pymongo import DESCENDING

from ..config.mongo import get_mongo_db
from ..utils.helpers import utcnow_iso
from . import uckr_service

log = logging.getLogger("gen-transform.transform")

VALID_TYPES = ("linkedin", "twitter", "advisory", "executive_summary",
               "infographic", "presentation", "video")


def _owner_filter(uid: str) -> dict:
    return {"$or": [{"firebaseUid": uid}, {"userId": uid}]}


def _top(uckr: dict, key: str, n: int) -> list[dict]:
    return (uckr.get(key) or [])[:n]


def _fact_values(uckr: dict, n: int = 6) -> list[str]:
    return [f["value"] for f in _top(uckr, "facts", n) if f.get("value")]


def _mark_used(uckr: dict, dtype: str) -> None:
    for f in uckr.get("facts", [])[:12]:
        used = f.setdefault("usedInDeliverables", [])
        if dtype not in used:
            used.append(dtype)


def _gen(dtype: str, uckr: dict, cfg: dict) -> dict:
    facts = _fact_values(uckr)
    metrics = _top(uckr, "metrics", 5)
    actions = _top(uckr, "actions", 5)
    entities = [e.get("name", "") for e in _top(uckr, "entities", 5) if e.get("name")]
    events = _top(uckr, "events", 4)
    audience = cfg.get("audience", "executive")
    tone = cfg.get("tone", "professional")
    language = cfg.get("language", "English")
    title = (uckr.get("summary", "")[:90] or "Key update").strip()

    if dtype == "linkedin":
        return {"hook": title or "What you need to know today",
                "body": "\n".join(f"• {v}" for v in facts[:5]),
                "callToAction": "Follow for more intelligence briefings.",
                "hashtags": ["ThreatIntel", "CyberSecurity", "ExecutiveBrief"],
                "characterCount": sum(len(v) for v in facts[:5]),
                "targetAudience": audience, "tone": tone, "language": language}
    if dtype == "twitter":
        thread = [{"index": i + 1, "text": v[:270], "charCount": min(len(v), 270)}
                  for i, v in enumerate(facts[:5])]
        return {"singlePost": (facts[0][:277] if facts else "Update"), "thread": thread}
    if dtype == "advisory":
        sev = "HIGH" if any("critical" in v.lower() or "risk" in v.lower() for v in facts) else "MEDIUM"
        return {"advisoryId": f"ADV-{uuid.uuid4().hex[:6].upper()}",
                "title": title or "Security Advisory",
                "severity": sev, "dateIssued": utcnow_iso()[:10],
                "situation": uckr.get("summary", ""),
                "keyInformation": facts[:6],
                "threatImpact": "; ".join(facts[1:3]) if len(facts) > 1 else "",
                "recommendedActions": [{"phase": "Immediate",
                                        "steps": [a.get("action", "") for a in actions[:4]]}],
                "entities": entities,
                "complianceReferences": []}
    if dtype == "executive_summary":
        return {"priority": "High" if metrics else "Medium",
                "keyFindingsCount": len(facts[:5]), "recommendationsCount": len(actions[:4]),
                "executiveOverview": uckr.get("summary", ""),
                "keyFindings": [{"metric": (metrics[i].get("value", "") if i < len(metrics) else ""),
                                 "title": v[:90], "description": v} for i, v in enumerate(facts[:5])],
                "implications": facts[2:5] if len(facts) > 2 else [],
                "strategicActions": [a.get("action", "") for a in actions[:4]]}
    if dtype == "infographic":
        return {"keyMessage": title or "At a glance",
                "keyStatistics": [{"value": m.get("value", ""), "label": m.get("name", "")[:60],
                                   "subtext": (m.get("context", "") or "")[:80]} for m in metrics[:4]],
                "supportingPoints": [{"iconName": "shield", "title": v[:60], "description": v}
                                      for v in facts[1:5]],
                "callToAction": "Share this briefing with your team.",
                "layoutRecommendation": "Vertical", "visualStyle": "Corporate"}
    if dtype == "presentation":
        slides = [{"slideNumber": 1, "title": title or "Briefing", "bullets": facts[:4],
                   "visualRecommendation": "Title visual", "speakerNotes": uckr.get("summary", "")}]
        for i, v in enumerate(facts[1:5], start=2):
            slides.append({"slideNumber": i, "title": v[:70], "bullets": [v],
                           "visualRecommendation": "Supporting chart",
                           "speakerNotes": v})
        if actions:
            slides.append({"slideNumber": len(slides) + 1, "title": "Recommended actions",
                           "bullets": [a.get("action", "") for a in actions[:4]],
                           "visualRecommendation": "Checklist visual", "speakerNotes": ""})
        return {"deckTitle": title or "Briefing deck", "totalSlides": len(slides), "slides": slides,
                "events": [{"title": e.get("title", ""), "timestamp": e.get("timestamp", "")} for e in events]}
    if dtype == "video":
        scenes = [{"sceneNumber": i + 1, "title": v[:60], "durationSeconds": 20,
                   "sceneDescription": v, "visualRecommendation": "Kinetic text over imagery",
                   "narration": v, "onScreenText": v[:80]} for i, v in enumerate(facts[:4])]
        total = sum(s["durationSeconds"] for s in scenes)
        return {"title": title or "Video briefing", "aspectRatio": "16:9", "style": "Professional",
                "totalDurationSeconds": total,
                "script": "\n\n".join(s["narration"] for s in scenes),
                "scenes": scenes, "subtitlesSrt": ""}
    raise HTTPException(status_code=422, detail=f"Unknown deliverable type: {dtype}")


def generate(
    uid: str, project_id: str, uckr_version: Optional[int], dtype: str, config: Optional[dict] = None
) -> dict:
    """Generate ONE deliverable from the project's UCKR and persist it."""
    from .project_service import get_project

    if dtype not in VALID_TYPES:
        raise HTTPException(status_code=422, detail=f"Unknown type. Valid: {list(VALID_TYPES)}.")
    project = get_project(project_id, uid)
    filt: dict[str, Any] = {"projectId": project_id, **_owner_filter(uid)}
    if uckr_version is not None:
        filt["version"] = uckr_version
    uckr = get_mongo_db()["uckr"].find_one(filt, sort=[("version", DESCENDING)])
    if not uckr:
        raise HTTPException(status_code=404, detail="No UCKR found — run analysis first.")
    uckr.pop("_id", None)

    content = _gen(dtype, uckr, config or {})
    _mark_used(uckr, dtype)
    now = utcnow_iso()
    doc = {
        "deliverableId": f"del-{uuid.uuid4().hex[:12]}",
        "firebaseUid": uid,
        "userId": uid,
        "projectId": project_id,
        "sourceId": uckr.get("sourceId", ""),
        "uckrVersion": uckr.get("version", 1),
        "type": dtype,
        "content": content,
        "configuration": config or {"audience": "executive", "tone": "professional",
                                    "language": "English", "detailLevel": "medium"},
        "status": "completed",
        "storagePath": None,
        "createdAt": now,
        "updatedAt": now,
    }
    col = get_mongo_db()["deliverables"]
    col.insert_one({**doc})
    # record grounding usage on the UCKR
    get_mongo_db()["uckr"].update_one(
        {"uckrId": uckr.get("uckrId")}, {"$set": {"facts": uckr.get("facts", [])}}
    )
    doc.pop("_id", None)
    log.info("deliverable generated project=%s type=%s uckrV=%s", project_id, dtype, doc["uckrVersion"])
    return doc


def generate_many(uid: str, project_id: str, types: list[str], config: Optional[dict] = None) -> list[dict]:
    """Generate all requested deliverables from the SAME UCKR version (Phase 5 fan-out)."""
    from .project_service import get_project

    get_project(project_id, uid)
    uckr = get_mongo_db()["uckr"].find_one(
        {"projectId": project_id, **_owner_filter(uid)}, sort=[("version", DESCENDING)]
    )
    if not uckr:
        raise HTTPException(status_code=404, detail="No UCKR found — run analysis first.")
    out = [generate(uid, project_id, int(uckr.get("version", 1)), t, config) for t in types]
    # also update the project's embedded deliverables snapshot for the frontend
    try:
        from .project_service import update_project

        snapshot = {d["type"]: d["content"] for d in out}
        update_project(project_id, {"deliverables": snapshot, "status": "completed"}, uid)
    except Exception as exc:
        log.warning("project deliverables snapshot skipped: %s", exc)
    return out


def list_deliverables(uid: str, project_id: str) -> list[dict]:
    from .project_service import get_project

    get_project(project_id, uid)
    cur = get_mongo_db()["deliverables"].find(
        {"projectId": project_id, **_owner_filter(uid)}, {"_id": 0}
    ).sort("createdAt", DESCENDING)
    return list(cur)


# --- legacy shim (kept for old route shape) ---
def run_pipeline(source: dict, config: dict, selected_outputs: list) -> dict:
    text = (source or {}).get("extractedText", "") or (source or {}).get("text", {}).get("content", "")
    if not text.strip():
        return {"status": "failed", "error": "No source text provided.", "deliverables": {}}
    analysis = __import__("app.services.ai_orchestrator", fromlist=["analyze_text"]).analyze_text(text)
    uckr = uckr_service.build_uckr(
        {"pages": [{"pageNumber": 1, "text": text}], "document": {"name": (source or {}).get("name", "source")}},
        analysis, uid="legacy", project_id="legacy", source_id="legacy",
    )
    deliverables = {}
    for t in (selected_outputs or [])[:7]:
        if t in VALID_TYPES:
            deliverables[t] = _gen(t, uckr, config or {})
    return {"status": "completed", "deliverables": deliverables,
            "analysis": {"summary": analysis.get("summary", "")}, "uckr": uckr}
