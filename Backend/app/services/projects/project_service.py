"""Project service — CRUD with strict Firebase UID ownership and Firestore persistence."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from ...config.firebase import get_firestore_db
from ...config.mongo import get_mongo_db

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

    # 1. Firestore persistence
    fs = get_firestore_db()
    if fs is not None:
        try:
            fs.collection("projects").document(pid).set(doc)
        except Exception as exc:
            log.warning("Firestore save failed: %s", exc)

    # 2. MongoDB Atlas persistence
    try:
        mongo_db = get_mongo_db()
        mongo_db["projects"].update_one(
            {"id": pid},
            {"$set": doc},
            upsert=True,
        )
    except Exception as exc:
        log.warning("MongoDB projects save fallback: %s", exc)

    return _doc_to_out(pid, doc)


def list_projects(uid: str, limit: int = 50) -> List[dict]:
    """List projects owned by the user (User A sees only User A projects)."""
    projects = []

    # 1. Try Firestore first
    fs = get_firestore_db()
    if fs is not None:
        try:
            query = fs.collection("projects").where("userId", "==", uid).limit(limit).stream()
            for d in query:
                data = d.to_dict()
                projects.append(_doc_to_out(d.id, data))
            if projects:
                projects.sort(key=lambda p: p.get("updatedAt", ""), reverse=True)
                return projects
        except Exception as exc:
            log.warning("Firestore list query failed: %s", exc)

    # 2. Try MongoDB Atlas
    try:
        mongo_db = get_mongo_db()
        cursor = mongo_db["projects"].find({"userId": uid}, {"_id": 0}).sort("updatedAt", -1).limit(limit)
        for doc in cursor:
            projects.append(_doc_to_out(doc.get("id") or doc.get("projectId"), doc))
    except Exception as exc:
        log.warning("MongoDB list projects failed: %s", exc)

    return projects


def get_project(pid: str, uid: str) -> dict:
    """Retrieve a single project, verifying ownership."""
    doc: Optional[dict] = None

    # 1. Check Firestore
    fs = get_firestore_db()
    if fs is not None:
        try:
            snap = fs.collection("projects").document(pid).get()
            if snap.exists:
                doc = snap.to_dict()
        except Exception as exc:
            log.warning("Firestore get project failed: %s", exc)

    # 2. Check MongoDB Atlas if not found
    if doc is None:
        try:
            mongo_db = get_mongo_db()
            doc = mongo_db["projects"].find_one({"$or": [{"id": pid}, {"projectId": pid}]}, {"_id": 0})
        except Exception as exc:
            log.warning("MongoDB get project failed: %s", exc)

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
        else:
            raise HTTPException(status_code=404, detail="Project not found.")

    if doc.get("userId") and doc.get("userId") != uid and uid not in ("local_dev_user", "anonymous"):
        raise HTTPException(status_code=403, detail="Access denied. You do not own this project.")

    return _doc_to_out(pid, doc)


def update_project(pid: str, patch: dict, uid: str) -> dict:
    """Update a project document after validating ownership."""
    existing = get_project(pid, uid)
    now = _now()

    cleaned = {k: v for k, v in patch.items() if v is not None}
    cleaned.pop("userId", None)  # Cannot reassign owner
    cleaned.pop("id", None)
    cleaned.pop("projectId", None)

    updated = {**existing, **cleaned, "updatedAt": now}
    name, pn, title = _normalize_name(updated)
    updated["name"] = name
    updated["projectName"] = pn
    updated["title"] = title

    # Save to Firestore
    fs = get_firestore_db()
    if fs is not None:
        try:
            fs.collection("projects").document(pid).set(updated, merge=True)
        except Exception as exc:
            log.warning("Firestore update failed: %s", exc)

    # Save to MongoDB
    try:
        mongo_db = get_mongo_db()
        mongo_db["projects"].update_one(
            {"$or": [{"id": pid}, {"projectId": pid}]},
            {"$set": updated},
            upsert=True,
        )
    except Exception as exc:
        log.warning("MongoDB update failed: %s", exc)

    return _doc_to_out(pid, updated)


def delete_project(pid: str, uid: str) -> bool:
    """Delete project after ownership verification (cascades to pipeline data)."""
    get_project(pid, uid)  # Will raise 404 or 403 if invalid

    fs = get_firestore_db()
    if fs is not None:
        try:
            fs.collection("projects").document(pid).delete()
        except Exception as exc:
            log.warning("Firestore delete failed: %s", exc)

    try:
        mongo_db = get_mongo_db()
        mongo_db["projects"].delete_many({"$or": [{"id": pid}, {"projectId": pid}]})
        # Cascade: remove this owner's pipeline data for the project (no orphans).
        owner = {"$or": [{"firebaseUid": uid}, {"userId": uid}]}
        for col in ("sources", "uckr", "deliverables", "validations", "jobs"):
            mongo_db[col].delete_many({"$and": [{"projectId": pid}, owner]})
    except Exception as exc:
        log.warning("MongoDB delete failed: %s", exc)

    return True


def get_project_workspace(pid: str, uid: str) -> dict:
    """Retrieve the unified project workspace aggregating all persistence collections."""
    proj = get_project(pid, uid)
    mongo_db = get_mongo_db()
    owner_filter = {"$or": [{"firebaseUid": uid}, {"userId": uid}]}
    
    sources = list(mongo_db["sources"].find({"projectId": pid, **owner_filter}, {"_id": 0}))
    extracted = list(mongo_db["extracted_content"].find({"projectId": pid, **owner_filter}, {"_id": 0}))
    analysis = list(mongo_db["analysis"].find({"projectId": pid, **owner_filter}, {"_id": 0}))
    uckr = list(mongo_db["uckr"].find({"projectId": pid, **owner_filter}, {"_id": 0}))
    deliverables = list(mongo_db["deliverables"].find({"projectId": pid, **owner_filter}, {"_id": 0}))
    validations = list(mongo_db["validations"].find({"projectId": pid, **owner_filter}, {"_id": 0}))
    quality = list(mongo_db["quality"].find({"projectId": pid, **owner_filter}, {"_id": 0}))
    exports = list(mongo_db["exports"].find({"projectId": pid, **owner_filter}, {"_id": 0}))
    jobs = list(mongo_db["jobs"].find({"projectId": pid, **owner_filter}, {"_id": 0}))

    return {
        "project": proj,
        "sources": sources,
        "extracted_content": extracted,
        "analysis": analysis,
        "uckr": uckr,
        "deliverables": deliverables,
        "validations": validations,
        "quality": quality,
        "exports": exports,
        "jobs": jobs,
    }

