"""Export API Routes (Phase 10 — Multi-Format Exporter & GridFS Delivery)."""
from __future__ import annotations

import io
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse

from ...auth import get_current_user
from ...services.export.schemas import ExportRequest
from ...services.export.export_service import (
    export_deliverable_artifact,
    get_export_record,
    list_project_exports,
    approve_deliverable,
)
from ...services.storage.gridfs_service import download_gridfs_file

router = APIRouter(prefix="/api/projects/{project_id}", tags=["Phase 10 Export"])


def _extract_uid(user: Any) -> str:
    if isinstance(user, dict):
        return str(user.get("uid") or user.get("userId") or "")
    return str(getattr(user, "uid", ""))


@router.post("/deliverables/{deliverable_id}/export")
async def export_deliverable(
    project_id: str,
    deliverable_id: str,
    payload: ExportRequest,
    user: Any = Depends(get_current_user),
):
    """Export a deliverable into a downloadable file format (pptx, docx, pdf, txt, mp3) stored in GridFS."""
    uid = _extract_uid(user)
    record = await export_deliverable_artifact(
        uid=uid,
        project_id=project_id,
        deliverable_id=deliverable_id,
        fmt=payload.format,
        require_approval=payload.require_approval,
        custom_title=payload.custom_title,
    )
    return {"ok": True, "export": record}


@router.post("/deliverables/{deliverable_id}/approve")
async def approve_deliverable_endpoint(
    project_id: str,
    deliverable_id: str,
    user: Any = Depends(get_current_user),
):
    """Approve deliverable for official enterprise export."""
    uid = _extract_uid(user)
    return approve_deliverable(project_id, deliverable_id, uid)


@router.get("/exports")
async def list_exports(
    project_id: str,
    user: Any = Depends(get_current_user),
):
    """List all exports for a project."""
    uid = _extract_uid(user)
    items = list_project_exports(project_id, uid)
    return {"ok": True, "exports": items, "count": len(items)}


@router.get("/exports/{export_id}")
async def get_export(
    project_id: str,
    export_id: str,
    user: Any = Depends(get_current_user),
):
    """Get metadata for a specific export."""
    uid = _extract_uid(user)
    doc = get_export_record(project_id, export_id, uid)
    return {"ok": True, "export": doc}


@router.get("/exports/{export_id}/download")
async def download_export_file(
    project_id: str,
    export_id: str,
    inline: bool = Query(False, description="View inline in browser if supported"),
    user: Any = Depends(get_current_user),
):
    """Download export binary stream directly from MongoDB GridFS with strict tenant security."""
    uid = _extract_uid(user)
    # 1. Load export metadata & verify ownership
    export = get_export_record(project_id, export_id, uid)
    file_id = export.get("fileId")
    if not file_id:
        raise HTTPException(status_code=404, detail="File binary ID not found on export record.")

    # 2. Download from GridFS
    data_bytes, meta = download_gridfs_file(file_id, uid=uid)
    filename = export.get("filename") or meta.get("filename", "export.bin")
    content_type = export.get("mimeType") or meta.get("contentType", "application/octet-stream")
    disposition = "inline" if inline else f'attachment; filename="{filename}"'

    return StreamingResponse(
        io.BytesIO(data_bytes),
        media_type=content_type,
        headers={
            "Content-Disposition": disposition,
            "Content-Length": str(len(data_bytes)),
            "X-ContentForge-Export-ID": export_id,
            "X-ContentForge-Deliverable-ID": export.get("deliverableId", ""),
        },
    )
