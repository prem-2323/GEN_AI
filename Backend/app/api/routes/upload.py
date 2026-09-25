"""Upload API routes for projects and standalone documents."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..dependencies import get_current_user
from ...core.exceptions import AppException
from ...core.logging import get_logger
from ...ingestion.service import ingestion_service

log = get_logger("api.upload")

router = APIRouter(tags=["upload"])


@router.post("/api/projects/{project_id}/upload")
async def upload_project_source(
    project_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Upload a source document to a project and run extraction."""
    uid = user["uid"]
    filename = file.filename or "upload.bin"
    contents = await file.read()

    try:
        return ingestion_service.process_project_upload(
            project_id=project_id,
            uid=uid,
            filename=filename,
            content_bytes=contents,
            content_type=file.content_type or "",
        )
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception as exc:
        log.error("Unexpected error in project source upload: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/api/upload")
async def upload_source(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Standalone lightweight source upload & extraction endpoint."""
    filename = file.filename or "source.txt"
    contents = await file.read()

    try:
        return ingestion_service.process_standalone_upload(
            filename=filename,
            content_bytes=contents,
            content_type=file.content_type or "",
        )
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception as exc:
        log.error("Unexpected error in standalone source upload: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
