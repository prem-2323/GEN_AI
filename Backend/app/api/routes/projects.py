"""Projects API routes with per-user ownership protection."""
from __future__ import annotations

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query

from ..auth import get_current_user
from ...models.project import ProjectCreate, ProjectUpdate, ProjectOut
from ...services import project_service
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
