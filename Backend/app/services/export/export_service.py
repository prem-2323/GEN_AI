"""Export Service — governance, generation, GridFS persistence, and lineage tracking (Phase 10)."""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from pymongo import DESCENDING

from ...config.mongo import get_mongo_db
from ...utils.helpers import utcnow_iso
from ..storage.gridfs_service import upload_gridfs_file, download_gridfs_file, delete_gridfs_file
from .export_manager import get_export_manager
from .schemas import ExportRecord

log = logging.getLogger("gen-transform.export.service")


def _owner_filter(uid: str) -> dict:
    return {"$or": [{"firebaseUid": uid}, {"userId": uid}]}


def _deliv_filter(deliverable_id: str, uid: str, project_id: Optional[str] = None) -> dict:
    match_id = {"$or": [{"deliverableId": deliverable_id}, {"id": deliverable_id}, {"_id": deliverable_id}]}
    match_owner = _owner_filter(uid)
    clauses = [match_id, match_owner]
    if project_id:
        clauses.append({"projectId": project_id})
    return {"$and": clauses}


async def export_deliverable_artifact(
    uid: str,
    project_id: str,
    deliverable_id: str,
    fmt: str = "docx",
    require_approval: bool = False,
    custom_title: Optional[str] = None,
) -> Dict[str, Any]:
    """Governance pipeline to export a deliverable into a downloadable file stored in GridFS."""
    db = get_mongo_db()
    fmt = fmt.lower().strip(".")

    # 1. Load deliverable & verify ownership
    deliv = db["deliverables"].find_one(_deliv_filter(deliverable_id, uid, project_id), {"_id": 0})
    if not deliv:
        deliv = db["deliverables"].find_one(_deliv_filter(deliverable_id, uid), {"_id": 0})
    if not deliv:
        other = db["deliverables"].find_one({"$or": [{"deliverableId": deliverable_id}, {"id": deliverable_id}, {"_id": deliverable_id}]})
        if other:
            raise HTTPException(status_code=403, detail="Access denied. You do not own this deliverable.")
        raise HTTPException(status_code=404, detail="Deliverable not found.")

    deliv_id = deliv.get("deliverableId") or deliv.get("id") or deliverable_id
    project_id = deliv.get("projectId") or project_id

    # 2. Load associated UCKR knowledge base for lineage
    uckr_v = deliv.get("uckrVersion", 1)
    uckr = db["uckr"].find_one(
        {"$and": [{"projectId": project_id}, {"version": uckr_v}, _owner_filter(uid)]},
        {"_id": 0},
    )
    if not uckr:
        uckr = db["uckr"].find_one(
            {"$and": [{"projectId": project_id}, _owner_filter(uid)]},
            sort=[("version", DESCENDING)],
            projection={"_id": 0},
        )

    # 3. Governance / Approval Check
    if require_approval:
        is_approved = bool((deliv.get("approval") or {}).get("approved", False))
        if not is_approved:
            qual = db["quality"].find_one(
                {"$or": [{"deliverableId": deliv_id}, {"id": deliv_id}, {"deliverableId": deliverable_id}]}
            )
            if qual and qual.get("approval", {}).get("approved", False):
                is_approved = True
        if not is_approved:
            raise HTTPException(
                status_code=412,
                detail="Deliverable has not been approved for official export. Please approve or disable require_approval.",
            )

    # 4. Generate binary file through ExportManager
    manager = get_export_manager()
    try:
        file_bytes, mime_type, filename = await manager.generate_export(
            deliverable=deliv,
            fmt=fmt,
            uckr=uckr,
            custom_title=custom_title,
        )
    except Exception as exc:
        log.error("Failed to generate export %s for %s: %s", fmt, deliv_id, exc)
        raise HTTPException(status_code=500, detail=f"Export generation failed: {exc}")

    # 5. Persist binary into MongoDB GridFS
    file_id = upload_gridfs_file(
        uid=uid,
        project_id=project_id,
        filename=filename,
        data=file_bytes,
        content_type=mime_type,
        file_type="export",
        deliverable_id=deliv_id,
        source_id=deliv.get("sourceId"),
        extra_meta={"exportFormat": fmt, "uckrVersion": uckr_v},
    )

    # 6. Save metadata to MongoDB `exports` collection
    export_id = f"exp_{deliv_id}_{fmt}_{uuid.uuid4().hex[:6]}"
    now = utcnow_iso()
    export_doc = {
        "_id": export_id,
        "exportId": export_id,
        "firebaseUid": uid,
        "userId": uid,
        "projectId": project_id,
        "sourceId": deliv.get("sourceId"),
        "deliverableId": deliv_id,
        "uckrId": uckr.get("uckrId") or uckr.get("id") if uckr else None,
        "uckrVersion": uckr_v,
        "exportType": fmt,
        "filename": filename,
        "mimeType": mime_type,
        "fileId": file_id,
        "fileSize": len(file_bytes),
        "status": "completed",
        "createdAt": now,
        "updatedAt": now,
    }

    db["exports"].update_one(
        {"exportId": export_id},
        {"$set": {k: v for k, v in export_doc.items() if k != "_id"}, "$setOnInsert": {"_id": export_id}},
        upsert=True,
    )

    # Update deliverable record with latest export link
    db["deliverables"].update_one(
        {"$or": [{"deliverableId": deliv_id}, {"id": deliv_id}]},
        {"$set": {f"exports.{fmt}": file_id, "latestExportId": export_id, "updatedAt": now}},
    )

    log.info("Completed Phase 10 export: id=%s deliv=%s fmt=%s gridfs_fileId=%s bytes=%d", export_id, deliv_id, fmt, file_id, len(file_bytes))
    return export_doc


def get_export_record(project_id: str, export_id: str, uid: str) -> Dict[str, Any]:
    """Retrieve metadata of a specific export."""
    db = get_mongo_db()
    doc = db["exports"].find_one(
        {"$and": [{"exportId": export_id}, _owner_filter(uid)]},
        {"_id": 0},
    )
    if not doc:
        other = db["exports"].find_one({"exportId": export_id})
        if other:
            raise HTTPException(status_code=403, detail="Access denied. You do not own this export.")
        raise HTTPException(status_code=404, detail="Export record not found.")
    return doc


def list_project_exports(project_id: str, uid: str, limit: int = 50) -> List[Dict[str, Any]]:
    """List all exports for a project."""
    db = get_mongo_db()
    cursor = db["exports"].find(
        {"$and": [{"projectId": project_id}, _owner_filter(uid)]},
        {"_id": 0},
    ).sort("createdAt", DESCENDING).limit(limit)
    return list(cursor)


def approve_deliverable(project_id: str, deliverable_id: str, uid: str) -> Dict[str, Any]:
    """Mark a deliverable as approved in both deliverables and quality collections."""
    db = get_mongo_db()
    deliv = db["deliverables"].find_one(_deliv_filter(deliverable_id, uid, project_id), {"_id": 0})
    if not deliv:
        deliv = db["deliverables"].find_one(_deliv_filter(deliverable_id, uid), {"_id": 0})
    if not deliv:
        raise HTTPException(status_code=404, detail="Deliverable not found.")

    deliv_id = deliv.get("deliverableId") or deliv.get("id") or deliverable_id
    now = utcnow_iso()
    
    db["deliverables"].update_one(
        {"$or": [{"_id": deliv_id}, {"deliverableId": deliv_id}, {"id": deliv_id}]},
        {"$set": {"approval": {"status": "approved", "approved": True, "approvedAt": now}, "updatedAt": now}},
    )
    db["quality"].update_one(
        {"$or": [{"_id": deliv_id}, {"deliverableId": deliv_id}, {"id": deliv_id}]},
        {
            "$set": {
                "deliverableId": deliv_id,
                "id": deliv_id,
                "projectId": project_id,
                "firebaseUid": uid,
                "userId": uid,
                "approval": {"status": "approved", "approved": True, "approvedAt": now},
                "updatedAt": now,
            },
            "$setOnInsert": {
                "_id": f"qual_{deliv_id}",
                "qualityId": f"qual_{deliv_id}",
                "createdAt": now,
            },
        },
        upsert=True,
    )
    return {"ok": True, "deliverableId": deliv_id, "approved": True, "approvedAt": now}
