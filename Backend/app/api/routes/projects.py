"""Projects API routes with per-user ownership protection."""
from __future__ import annotations

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query

from ...auth import get_current_user
from ...models.project import ProjectCreate, ProjectUpdate, ProjectOut
from ...services.projects import project_service
from ...utils.helpers import is_valid_id

router = APIRouter(tags=["projects"])


def _validate_project_id(project_id: str):
    if not is_valid_id(project_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid project ID format (allowed: a-zA-Z0-9_-, max 128 characters).",
        )


@router.post("/api/projects", response_model=ProjectOut, status_code=201)
@router.post("/projects", response_model=ProjectOut, status_code=201, include_in_schema=False)
async def create_project(payload: ProjectCreate, user: dict = Depends(get_current_user)):
    """Create a new project owned by the authenticated Firebase user."""
    data = payload.model_dump(exclude_unset=False, exclude_none=False)
    name = (data.get("name") or data.get("projectName") or data.get("title") or "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="Project name (or title) is required.")

    if data.get("id"):
        _validate_project_id(data["id"])

    return project_service.create_project(data, uid=user["uid"])


@router.get("/api/projects", response_model=List[ProjectOut])
@router.get("/projects", response_model=List[ProjectOut], include_in_schema=False)
async def list_projects(
    user: dict = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100),
):
    """List all projects belonging strictly to the authenticated Firebase user."""
    return project_service.list_projects(uid=user["uid"], limit=limit)


@router.get("/api/projects/{project_id}", response_model=ProjectOut)
@router.get("/projects/{project_id}", response_model=ProjectOut, include_in_schema=False)
async def get_project(project_id: str, user: dict = Depends(get_current_user)):
    """Get project details if owned by the authenticated user."""
    _validate_project_id(project_id)
    return project_service.get_project(project_id, uid=user["uid"])


@router.put("/api/projects/{project_id}", response_model=ProjectOut)
@router.put("/projects/{project_id}", response_model=ProjectOut, include_in_schema=False)
async def update_project(
    project_id: str,
    payload: ProjectUpdate,
    user: dict = Depends(get_current_user),
):
    """Update project fields with ownership verification."""
    _validate_project_id(project_id)
    patch = payload.model_dump(exclude_unset=True)
    return project_service.update_project(project_id, patch, uid=user["uid"])


@router.delete("/api/projects/{project_id}")
@router.delete("/projects/{project_id}", include_in_schema=False)
async def delete_project(project_id: str, user: dict = Depends(get_current_user)):
    """Delete project with ownership verification."""
    _validate_project_id(project_id)
    project_service.delete_project(project_id, uid=user["uid"])
    return {"ok": True, "deleted": project_id}


@router.get("/api/projects/{project_id}/workspace")
@router.get("/projects/{project_id}/workspace", include_in_schema=False)
async def get_project_workspace(project_id: str, user: dict = Depends(get_current_user)):
    """Retrieve full aggregated project workspace state (sources, UCKR, deliverables, validations, quality, exports)."""
    _validate_project_id(project_id)
    return project_service.get_project_workspace(project_id, uid=user["uid"])


@router.get("/api/projects/{project_id}/files/{file_id}/download")
@router.get("/projects/{project_id}/files/{file_id}/download", include_in_schema=False)
async def download_project_file(
    project_id: str,
    file_id: str,
    user: dict = Depends(get_current_user),
    inline: bool = Query(False),
):
    """Download project-scoped file directly from storage abstraction with tenant security."""
    import io
    from fastapi.responses import StreamingResponse
    from ...storage import get_storage

    _validate_project_id(project_id)
    # Verifies user owns the project first
    project_service.get_project(project_id, uid=user["uid"])

    storage = get_storage()
    # Support direct key or file_id lookups
    file_key = f"documents/{project_id}/{file_id}" if not file_id.startswith("documents/") else file_id
    if not storage.exists(file_key):
        # Fallback check raw key
        file_key = file_id

    data_bytes, meta = storage.read(file_key)
    filename = meta.filename if meta else "download.bin"
    content_type = meta.content_type if meta else "application/octet-stream"
    disposition = "inline" if inline else f'attachment; filename="{filename}"'

    return StreamingResponse(
        io.BytesIO(data_bytes),
        media_type=content_type,
        headers={
            "Content-Disposition": disposition,
            "Content-Length": str(len(data_bytes)),
            "X-File-ID": file_id,
        },
    )

