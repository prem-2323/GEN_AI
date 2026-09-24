""" /projects CRUD — strict per-user isolation (User A <-> User B).

Firestore:
    projects/{projectId} = { id, userId, projectName, title, sourceFile|source,
                              status, config?, selectedOutputs?, analysis?, uckr?,
                              deliverables?, createdAt, updatedAt }

Rules enforced here (mirrors firestore.rules):
  - list/get/update/delete scoped to where userId == request.auth.uid
  - create forces userId = uid, id == doc id
  - cross-tenant access -> 403, missing -> 404
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from ..auth import get_current_user
from .. import firebase_admin as db
from ..models import ProjectCreate, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])

_ID_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_id(pid: str):
    if not pid or len(pid) > 128 or not _ID_RE.match(pid):
        raise HTTPException(status_code=400, detail="Invalid project id (a-zA-Z0-9_- , max 128).")


def _normalize_name(data: dict) -> tuple[str, str]:
    """Return (projectName, title) with both kept in sync for frontend compat."""
    pn = (data.get("projectName") or data.get("title") or "").strip() if isinstance(data.get("projectName") or data.get("title"), str) else (data.get("projectName") or data.get("title") or "")
    title = (data.get("title") or data.get("projectName") or "").strip() if isinstance(data.get("title") or data.get("projectName"), str) else (data.get("title") or data.get("projectName") or "")
    return str(pn or "Untitled Project"), str(title or pn or "Untitled Project")


def _to_out(pid: str, doc: dict) -> dict:
    pn, title = _normalize_name(doc)
    out = {**doc}
    out["id"] = pid
    out["projectName"] = pn
    out["title"] = title
    return out


@router.post("", status_code=201)
def create_project(payload: ProjectCreate, user: dict = Depends(get_current_user)):
    uid = user["uid"]
    data: dict[str, Any] = payload.model_dump(exclude_unset=False, exclude_none=False)
    pid = (data.get("id") or f"proj-{uuid.uuid4().hex[:12]}").strip()
    _validate_id(pid)

    name = (data.get("projectName") or data.get("title") or "").strip() if isinstance(data.get("projectName") or data.get("title"), str) else ""
    if not name:
        raise HTTPException(status_code=422, detail="projectName (or title) is required.")
    if len(name) > 300:
        raise HTTPException(status_code=422, detail="projectName/title max 300 chars.")
    desc = data.get("description") or ""
    if isinstance(desc, str) and len(desc) > 2000:
        raise HTTPException(status_code=422, detail="description max 2000 chars.")

    if db.db_get_project(pid) is not None:
        raise HTTPException(status_code=409, detail=f"Project {pid} already exists.")

    now = _now()
    pn, title = _normalize_name(data)
    source = data.get("source") if data.get("source") is not None else data.get("sourceFile")
    doc = {
        "id": pid,
        "userId": uid,  # ALWAYS force owner — ignore any client-supplied userId
        "projectName": pn,
        "title": title,
        "description": desc or "",
        "sourceFile": data.get("sourceFile"),
        "source": source,
        "status": data.get("status") or "Draft",
        "config": data.get("config"),
        "selectedOutputs": data.get("selectedOutputs"),
        "analysis": data.get("analysis"),
        "uckr": data.get("uckr"),
        "deliverables": data.get("deliverables"),
        "createdAt": now,
        "updatedAt": now,
    }
    # carry through any extra keys (future UCKR/deliverable blobs)
    known = set(doc.keys())
    for k, v in data.items():
        if k not in known and k not in ("id", "projectName"):
            doc[k] = v
    db.db_set_project(pid, doc)
    return _to_out(pid, doc)


@router.get("")
def list_projects(
    user: dict = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100),
):
    uid = user["uid"]
    return [_to_out(p.get("id", ""), p) for p in db.db_list_projects(uid, limit=limit)]


@router.get("/{project_id}")
def get_project(project_id: str, user: dict = Depends(get_current_user)):
    _validate_id(project_id)
    doc = db.db_get_project(project_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found.")
    if doc.get("userId") != user["uid"]:
        raise HTTPException(status_code=403, detail="Access denied (cross-tenant).")
    return _to_out(project_id, doc)


@router.put("/{project_id}")
def update_project(project_id: str, payload: ProjectUpdate, user: dict = Depends(get_current_user)):
    _validate_id(project_id)
    doc = db.db_get_project(project_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found.")
    if doc.get("userId") != user["uid"]:
        raise HTTPException(status_code=403, detail="Access denied (cross-tenant).")

    patch = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if "projectName" in patch or "title" in patch:
        merged = {**doc, **patch}
        pn, title = _normalize_name(merged)
        if len(pn) > 300 or len(title) > 300:
            raise HTTPException(status_code=422, detail="projectName/title max 300 chars.")
        patch["projectName"], patch["title"] = pn, title
    if "description" in patch and isinstance(patch["description"], str) and len(patch["description"]) > 2000:
        raise HTTPException(status_code=422, detail="description max 2000 chars.")
    if "sourceFile" in patch and "source" not in patch:
        patch["source"] = patch["sourceFile"]
    if "source" in patch and "sourceFile" not in patch:
        # keep both in sync when only one side sent
        patch.setdefault("sourceFile", patch["source"])

    patch.pop("userId", None)
    patch.pop("id", None)
    updated = {**doc, **patch, "id": project_id, "userId": user["uid"], "updatedAt": _now()}
    updated.setdefault("createdAt", doc.get("createdAt", _now()))
    db.db_set_project(project_id, updated)
    return _to_out(project_id, updated)


@router.delete("/{project_id}", status_code=200)
def delete_project(project_id: str, user: dict = Depends(get_current_user)):
    _validate_id(project_id)
    doc = db.db_get_project(project_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found.")
    if doc.get("userId") != user["uid"]:
        raise HTTPException(status_code=403, detail="Access denied (cross-tenant).")
    db.db_delete_project(project_id)
    return {"ok": True, "deleted": project_id}
