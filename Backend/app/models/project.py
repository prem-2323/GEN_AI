"""Project schemas."""
from __future__ import annotations

from typing import Any, List, Optional
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    id: Optional[str] = Field(default=None, description="Optional client-chosen project id")
    name: Optional[str] = None
    projectName: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = ""
    source: Optional[Any] = None
    sourceFile: Optional[Any] = None
    status: Optional[str] = "created"
    config: Optional[Any] = None
    selectedOutputs: Optional[List[str]] = Field(default_factory=list)
    analysis: Optional[Any] = None
    uckr: Optional[Any] = None
    deliverables: Optional[Any] = None

    model_config = {"extra": "allow"}


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    projectName: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    source: Optional[Any] = None
    sourceFile: Optional[Any] = None
    status: Optional[str] = None
    config: Optional[Any] = None
    selectedOutputs: Optional[List[str]] = None
    analysis: Optional[Any] = None
    uckr: Optional[Any] = None
    deliverables: Optional[Any] = None

    model_config = {"extra": "allow"}


class ProjectOut(BaseModel):
    projectId: str
    id: str
    userId: str
    name: str = ""
    projectName: str = ""
    title: str = ""
    description: str = ""
    status: str = "created"
    sourceCount: int = 0
    source: Optional[Any] = None
    sourceFile: Optional[Any] = None
    config: Optional[Any] = None
    selectedOutputs: Optional[List[str]] = Field(default_factory=list)
    analysis: Optional[Any] = None
    uckr: Optional[Any] = None
    deliverables: Optional[Any] = None
    createdAt: str = ""
    updatedAt: str = ""

    model_config = {"extra": "allow"}
