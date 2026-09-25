"""Project service — CRUD with application-level user ownership and database-independent repository."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from ...storage.repository import get_repository

log = logging.getLogger("gen-transform.project_service")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_name(data: dict) -> tuple[str, str, str]:
    """Extract and sync (name, projectName, title)."""
    raw_name = data.get("name") or data.get("projectName") or data.get("title") or "Untitled Project"
    name_str = str(raw_name).strip() if isinstance(raw_name, str) else "Untitled Project"
    return name_str, name_str, name_str


def _doc_to_out(pid: str, doc: dict) -> dict:
    name, pn, title = _normalize_name(doc)
    out = {**doc}
    out["projectId"] = pid
    out["id"] = pid
    out["name"] = name
    out["projectName"] = pn
    out["title"] = title
    out.setdefault("sourceCount", 1 if doc.get("source") or doc.get("sourceFile") else 0)
    out.setdefault("status", "created")
    return out


def create_project(data: dict, uid: str) -> dict:
    """Create a new project for the authenticated user."""
    pid = (data.get("id") or data.get("projectId") or f"proj-{uuid.uuid4().hex[:12]}").strip()
    name, pn, title = _normalize_name(data)
    now = _now()
    source = data.get("source") if data.get("source") is not None else data.get("sourceFile")

    doc: Dict[str, Any] = {
        "projectId": pid,
        "id": pid,
        "userId": uid,  # ALWAYS force owner UID
        "name": name,
        "projectName": pn,
        "title": title,
        "description": data.get("description", ""),
        "sourceFile": data.get("sourceFile"),
        "source": source,
        "sourceCount": 1 if source else 0,
        "status": data.get("status") or "created",
        "config": data.get("config"),
        "selectedOutputs": data.get("selectedOutputs") or [],
        "analysis": data.get("analysis"),
        "uckr": data.get("uckr"),
        "deliverables": data.get("deliverables"),
        "createdAt": now,
        "updatedAt": now,
    }

    # Pass through any extra keys
    known = set(doc.keys())
    for k, v in data.items():
        if k not in known:
            doc[k] = v

    repo = get_repository("projects")
    repo.update_one({"id": pid}, {"$set": doc}, upsert=True)

    return _doc_to_out(pid, doc)


def list_projects(uid: str, limit: int = 50) -> List[dict]:
    """List projects owned by the user."""
    repo = get_repository("projects")
    query = {"$or": [{"userId": uid}, {"firebaseUid": uid}]} if uid else {}
    docs = repo.find(query, sort=[("updatedAt", -1)], limit=limit, projection={"_id": 0})
    return [_doc_to_out(doc.get("id") or doc.get("projectId"), doc) for doc in docs]


def get_project(pid: str, uid: str) -> dict:
    """Retrieve a single project, verifying ownership."""
    repo = get_repository("projects")
    doc = repo.find_one({"$or": [{"id": pid}, {"projectId": pid}]}, projection={"_id": 0})

    if not doc:
        if pid in ("proj_default", "default") or pid.startswith("proj-") or pid.startswith("proj_"):
            # Auto-provision transient workspace project
            doc = {
                "projectId": pid,
                "id": pid,
                "userId": uid,
                "name": "Default Project",
                "projectName": "Default Project",
                "title": "Default Project",
                "status": "created",
                "createdAt": _now(),
                "updatedAt": _now(),
            }
            repo.update_one({"id": pid}, {"$set": doc}, upsert=True)
        else:
            raise HTTPException(status_code=404, detail="Project not found.")

    doc_owner = doc.get("userId") or doc.get("firebaseUid")
    if doc_owner and doc_owner != uid and uid not in ("local_dev_user", "anonymous"):
        raise HTTPException(status_code=403, detail="Access denied. You do not own this project.")

    return _doc_to_out(pid, doc)


def update_project(pid: str, patch: dict, uid: str) -> dict:
    """Update a project document after validating ownership."""
    existing = get_project(pid, uid)
    now = _now()

    cleaned = {k: v for k, v in patch.items() if v is not None}
    cleaned.pop("userId", None)  # Cannot reassign owner
    cleaned.pop("firebaseUid", None)
    cleaned.pop("id", None)
    cleaned.pop("projectId", None)

    updated = {**existing, **cleaned, "updatedAt": now}
    name, pn, title = _normalize_name(updated)
    updated["name"] = name
    updated["projectName"] = pn
    updated["title"] = title

    repo = get_repository("projects")
    repo.update_one({"$or": [{"id": pid}, {"projectId": pid}]}, {"$set": updated}, upsert=True)

    return _doc_to_out(pid, updated)


def delete_project(pid: str, uid: str) -> bool:
    """Delete project after ownership verification (cascades to pipeline data)."""
    try:
        get_project(pid, uid)
    except HTTPException as exc:
        if exc.status_code != 404:
            raise

    repo = get_repository("projects")
    repo.delete_many({"$or": [{"id": pid}, {"projectId": pid}]})

    # Cascade: remove this owner's pipeline data for the project
    owner = {"$or": [{"userId": uid}, {"firebaseUid": uid}]}
    for col_name in ("sources", "uckr", "doclink", "deliverables", "validations", "jobs", "extracted_content", "analysis", "quality", "exports"):
        col_repo = get_repository(col_name)
        col_repo.delete_many({"$and": [{"projectId": pid}, owner]})

    return True


def get_project_workspace(pid: str, uid: str) -> dict:
    """Retrieve the unified project workspace aggregating all persistence collections."""
    proj = get_project(pid, uid)
    owner_filter = {"$or": [{"userId": uid}, {"firebaseUid": uid}]}

    cols = ("sources", "extracted_content", "analysis", "uckr", "deliverables", "validations", "quality", "exports", "jobs")
    workspace_data = {"project": proj}

    for col in cols:
        col_repo = get_repository(col)
        workspace_data[col] = col_repo.find({"projectId": pid, **owner_filter}, projection={"_id": 0})

    return workspace_data


