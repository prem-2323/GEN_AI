"""Search & retrieval (Phase 11) — scoped full-text-style search over the
caller's own projects and sources. No vector DB: MongoDB regex search is
enough until scale demands more.
"""
from __future__ import annotations

import re
from typing import Optional

from pymongo import DESCENDING

from ..config.mongo import get_mongo_db


def _owner_filter(uid: str) -> dict:
    return {"$or": [{"firebaseUid": uid}, {"userId": uid}]}


def search(uid: str, q: str, kind: str = "all", limit: int = 20) -> dict:
    q = (q or "").strip()
    if not q:
        return {"query": "", "projects": [], "sources": []}
    rx = re.compile(re.escape(q), re.IGNORECASE)
    db = get_mongo_db()
    out: dict = {"query": q}
    if kind in ("all", "project"):
        out["projects"] = list(db["projects"].find(
            {"$and": [_owner_filter(uid), {"$or": [
                {"name": rx}, {"projectName": rx}, {"title": rx}, {"description": rx}]}]},
            {"_id": 0},
        ).sort("updatedAt", DESCENDING).limit(limit))
    if kind in ("all", "source"):
        out["sources"] = list(db["sources"].find(
            {"$and": [_owner_filter(uid), {"$or": [
                {"file.originalName": rx},
                {"normalized.text.content": rx},
                {"normalized.document.name": rx}]}]},
            {"_id": 0, "normalized": 0},
        ).sort("updatedAt", DESCENDING).limit(limit))
    return out


def project_overview(uid: str, project_id: str) -> dict:
    """Phase 9 bundle: project + sources + latest UCKR + deliverables + validations + jobs."""
    from .project_service import get_project
    from . import source_service

    project = get_project(project_id, uid)
    db = get_mongo_db()
    filt_owner = _owner_filter(uid)
    latest_uckr = db["uckr"].find_one({"projectId": project_id, **filt_owner},
                                      {"_id": 0}, sort=[("version", DESCENDING)])
    return {
        "project": project,
        "sources": source_service.list_sources(uid, project_id, limit=50),
        "uckr": latest_uckr,
        "deliverables": list(db["deliverables"].find(
            {"projectId": project_id, **filt_owner}, {"_id": 0}).sort("createdAt", DESCENDING).limit(50)),
        "validations": list(db["validations"].find(
            {"projectId": project_id, **filt_owner}, {"_id": 0}).sort("checkedAt", DESCENDING).limit(10)),
        "jobs": list(db["jobs"].find(
            {"projectId": project_id, **filt_owner}, {"_id": 0}).sort("createdAt", DESCENDING).limit(10)),
    }
