"""Search & retrieval (Phase 11) — scoped text search over the caller's own projects and sources."""
from __future__ import annotations

import re
from typing import Optional

from ...storage.repository import get_repository


def _owner_filter(uid: str) -> dict:
    return {"$or": [{"userId": uid}, {"firebaseUid": uid}]}


def search(uid: str, q: str, kind: str = "all", limit: int = 20) -> dict:
    q = (q or "").strip()
    if not q:
        return {"query": "", "projects": [], "sources": []}
    rx_str = re.escape(q)
    out: dict = {"query": q}

    if kind in ("all", "project"):
        proj_repo = get_repository("projects")
        query = {
            "$and": [
                _owner_filter(uid),
                {"$or": [{"name": {"$regex": rx_str}}, {"projectName": {"$regex": rx_str}}, {"title": {"$regex": rx_str}}, {"description": {"$regex": rx_str}}]}
            ]
        }
        out["projects"] = proj_repo.find(query, sort=[("updatedAt", -1)], limit=limit, projection={"_id": 0})

    if kind in ("all", "source"):
        src_repo = get_repository("sources")
        query = {
            "$and": [
                _owner_filter(uid),
                {"$or": [
                    {"originalFilename": {"$regex": rx_str}},
                    {"fileType": {"$regex": rx_str}},
                    {"name": {"$regex": rx_str}},
                    {"extractedText": {"$regex": rx_str}},
                    {"file.originalName": {"$regex": rx_str}},
                    {"file.storedName": {"$regex": rx_str}},
                ]}
            ]
        }
        sources = src_repo.find(query, sort=[("updatedAt", -1)], limit=limit, projection={"_id": 0})
        for s in sources:
            s.pop("normalized", None)
        out["sources"] = sources

    return out


def project_overview(uid: str, project_id: str) -> dict:
    """Phase 9 bundle: project + sources + latest UCKR + deliverables + validations + jobs."""
    from ..projects.project_service import get_project
    from ..sources import source_service

    project = get_project(project_id, uid)
    filt_owner = _owner_filter(uid)

    uckr_repo = get_repository("uckr")
    latest_uckr = uckr_repo.find_one({"projectId": project_id, **filt_owner}, sort=[("version", -1)], projection={"_id": 0})

    deliv_repo = get_repository("deliverables")
    deliverables = deliv_repo.find({"projectId": project_id, **filt_owner}, sort=[("createdAt", -1)], limit=50, projection={"_id": 0})

    val_repo = get_repository("validations")
    validations = val_repo.find({"projectId": project_id, **filt_owner}, sort=[("checkedAt", -1)], limit=10, projection={"_id": 0})

    job_repo = get_repository("jobs")
    jobs = job_repo.find({"projectId": project_id, **filt_owner}, sort=[("createdAt", -1)], limit=10, projection={"_id": 0})

    return {
        "project": project,
        "sources": source_service.list_sources(uid, project_id, limit=50),
        "uckr": latest_uckr,
        "deliverables": deliverables,
        "validations": validations,
        "jobs": jobs,
    }

