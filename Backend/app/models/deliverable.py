"""Deliverables model."""
from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel


class DeliverablesModel(BaseModel):
    linkedin: Optional[Dict[str, Any]] = None
    twitter: Optional[Dict[str, Any]] = None
    advisory: Optional[Dict[str, Any]] = None
    infographic: Optional[Dict[str, Any]] = None
    executive_summary: Optional[Dict[str, Any]] = None
    presentation: Optional[Dict[str, Any]] = None
    video: Optional[Dict[str, Any]] = None

    model_config = {"extra": "allow"}
