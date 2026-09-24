"""Pydantic models.

Canonical Firestore shapes:
    users/{uid}:        { userId, email, displayName?, photoURL?, createdAt, updatedAt }
    projects/{projectId}:{ id, userId, projectName, title, description?, sourceFile|source?,
                           status, config?, selectedOutputs?, analysis?, uckr?, deliverables?,
                           createdAt, updatedAt }
"""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class UserOut(BaseModel):
    userId: str
    email: str = ""
    displayName: str = ""
    photoURL: str = ""
    createdAt: str = ""
    updatedAt: str = ""


class ProjectCreate(BaseModel):
    """Accept BOTH minimal spec and full frontend payload."""

    id: Optional[str] = Field(default=None, description="Optional client-chosen doc id")
    # minimal spec names
    projectName: Optional[str] = None
    sourceFile: Optional[Any] = None
    # frontend names
    title: Optional[str] = None
    description: Optional[str] = None
    source: Optional[Any] = None
    status: Optional[str] = "Draft"
    config: Optional[Any] = None
    selectedOutputs: Optional[Any] = None
    analysis: Optional[Any] = None
    uckr: Optional[Any] = None
    deliverables: Optional[Any] = None

    # allow any extra UCKR / deliverable blobs to pass through
    model_config = {"extra": "allow"}


class ProjectUpdate(BaseModel):
    projectName: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    sourceFile: Optional[Any] = None
    source: Optional[Any] = None
    status: Optional[str] = None
    config: Optional[Any] = None
    selectedOutputs: Optional[Any] = None
    analysis: Optional[Any] = None
    uckr: Optional[Any] = None
    deliverables: Optional[Any] = None

    model_config = {"extra": "allow"}


class ProjectOut(BaseModel):
    id: str
    userId: str
    projectName: str = ""
    title: str = ""
    description: str = ""
    sourceFile: Any = None
    source: Any = None
    status: str = "Draft"
    config: Any = None
    selectedOutputs: Any = None
    analysis: Any = None
    uckr: Any = None
    deliverables: Any = None
    createdAt: str = ""
    updatedAt: str = ""

    model_config = {"extra": "allow"}
