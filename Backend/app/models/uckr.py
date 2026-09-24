"""UCKR and Deliverables models."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class UckrModel(BaseModel):
    stats: Optional[Dict[str, Any]] = None
    facts: Optional[List[Dict[str, Any]]] = None
    entities: Optional[List[Dict[str, Any]]] = None
    events: Optional[List[Dict[str, Any]]] = None
    metrics: Optional[List[Dict[str, Any]]] = None
    relationships: Optional[List[Dict[str, Any]]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    sources: Optional[List[Dict[str, Any]]] = None

    model_config = {"extra": "allow"}
