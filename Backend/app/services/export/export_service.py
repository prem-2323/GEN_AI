"""Export Service — governance, generation, file persistence, and lineage tracking (Phase 10)."""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional
from fastapi import HTTPException

from ...storage.repository import get_repository
from ...storage.service import save_output
from ...utils.helpers import utcnow_iso
from .export_manager import get_export_manager
from .schemas import ExportRecord

log = logging.getLogger("gen-transform.export.service")


def _owner_filter(uid: str) -> dict:
    return {"$or": [{"userId": uid}, {"firebaseUid": uid}]}


def _deliv_filter(deliverable_id: str, uid: str, project_id: Optional[str] = None) -> dict:
    match_id = {"$or": [{"deliverableId": deliverable_id}, {"id": deliverable_id}]}
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
    """Governance pipeline to export a deliverable into a downloadable file stored in file storage."""
    fmt = fmt.lower().strip(".")

    # 1. Load deliverable & verify ownership
    deliv_repo = get_repository("deliverables")
    deliv = deliv_repo.find_one(_deliv_filter(deliverable_id, uid, project_id), projection={"_id": 0})
    if not deliv:
        deliv = deliv_repo.find_one(_deliv_filter(deliverable_id, uid), projection={"_id": 0})
    if not deliv:
        other = deliv_repo.find_one({"$or": [{"deliverableId": deliverable_id}, {"id": deliverable_id}]}, projection={"_id": 0})
        if other:
            raise HTTPException(status_code=403, detail="Access denied. You do not own this deliverable.")
        raise HTTPException(status_code=404, detail="Deliverable not found.")

    deliv_id = deliv.get("deliverableId") or deliv.get("id") or deliverable_id
    project_id = deliv.get("projectId") or project_id

    # 2. Load associated UCKR knowledge base for lineage
    uckr_v = deliv.get("uckrVersion", 1)
    uckr_repo = get_repository("uckr")
    uckr = uckr_repo.find_one(
        {"$and": [{"projectId": project_id}, {"version": uckr_v}, _owner_filter(uid)]},
        projection={"_id": 0},
    )
    if not uckr:
        uckr = uckr_repo.find_one(
            {"$and": [{"projectId": project_id}, _owner_filter(uid)]},
            sort=[("version", -1)],
            projection={"_id": 0},
        )

    # 3. Governance / Approval Check
    if require_approval:
        is_approved = bool((deliv.get("approval") or {}).get("approved", False))
        if not is_approved:
            qual_repo = get_repository("quality")
            qual = qual_repo.find_one(
                {"$or": [{"deliverableId": deliv_id}, {"id": deliv_id}]},
                projection={"_id": 0},
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

    # 5. Persist binary into FileStorage
    file_id, rel_path = save_output(
        uid=uid,
        project_id=project_id,
        filename=filename,
        data=file_bytes,
        deliverable_id=deliv_id,
        export_type=fmt,
    )

    # 6. Save metadata to `exports` repository
    export_id = f"exp_{deliv_id}_{fmt}_{uuid.uuid4().hex[:6]}"
    now = utcnow_iso()
    export_doc = {
        "exportId": export_id,
        "id": export_id,
        "userId": uid,
        "firebaseUid": uid,
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
        "storagePath": rel_path,
        "status": "completed",
        "createdAt": now,
        "updatedAt": now,
    }

    exports_repo = get_repository("exports")
    exports_repo.update_one(
        {"exportId": export_id},
        {"$set": export_doc},
        upsert=True,
    )

    # Update deliverable record with latest export link
    deliv_repo.update_one(
        {"$or": [{"deliverableId": deliv_id}, {"id": deliv_id}]},
        {"$set": {f"exports.{fmt}": file_id, "latestExportId": export_id, "updatedAt": now}},
    )

    log.info("Completed Phase 10 export: id=%s deliv=%s fmt=%s fileId=%s bytes=%d", export_id, deliv_id, fmt, file_id, len(file_bytes))
    return export_doc


def get_export_record(project_id: str, export_id: str, uid: str) -> Dict[str, Any]:
    """Retrieve metadata of a specific export."""
    exports_repo = get_repository("exports")
    doc = exports_repo.find_one(
        {"$and": [{"$or": [{"exportId": export_id}, {"id": export_id}]}, _owner_filter(uid)]},
        projection={"_id": 0},
    )
    if not doc:
        other = exports_repo.find_one({"$or": [{"exportId": export_id}, {"id": export_id}]}, projection={"_id": 0})
        if other:
            raise HTTPException(status_code=403, detail="Access denied. You do not own this export.")
        raise HTTPException(status_code=404, detail="Export record not found.")
    return doc


def list_project_exports(project_id: str, uid: str, limit: int = 50) -> List[Dict[str, Any]]:
    """List all exports for a project."""
    exports_repo = get_repository("exports")
    return exports_repo.find(
        {"$and": [{"projectId": project_id}, _owner_filter(uid)]},
        sort=[("createdAt", -1)],
        limit=limit,
        projection={"_id": 0},
    )


def approve_deliverable(project_id: str, deliverable_id: str, uid: str) -> Dict[str, Any]:
    """Mark a deliverable as approved in both deliverables and quality collections."""
    deliv_repo = get_repository("deliverables")
    deliv = deliv_repo.find_one(_deliv_filter(deliverable_id, uid, project_id), projection={"_id": 0})
    if not deliv:
        deliv = deliv_repo.find_one(_deliv_filter(deliverable_id, uid), projection={"_id": 0})
    if not deliv:
        raise HTTPException(status_code=404, detail="Deliverable not found.")

    deliv_id = deliv.get("deliverableId") or deliv.get("id") or deliverable_id
    now = utcnow_iso()

    deliv_repo.update_one(
        {"$or": [{"deliverableId": deliv_id}, {"id": deliv_id}]},
        {"$set": {"approval": {"status": "approved", "approved": True, "approvedAt": now}, "updatedAt": now}},
    )
    qual_repo = get_repository("quality")
    qual_repo.update_one(
        {"$or": [{"deliverableId": deliv_id}, {"id": deliv_id}]},
        {
            "$set": {
                "deliverableId": deliv_id,
                "id": deliv_id,
                "projectId": project_id,
                "userId": uid,
                "firebaseUid": uid,
                "approval": {"status": "approved", "approved": True, "approvedAt": now},
                "updatedAt": now,
            },
            "$setOnInsert": {
                "qualityId": f"qual_{deliv_id}",
                "createdAt": now,
            },
        },
        upsert=True,
    )
    return {"ok": True, "deliverableId": deliv_id, "approved": True, "approvedAt": now}

