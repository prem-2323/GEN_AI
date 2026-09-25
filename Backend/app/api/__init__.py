"""API package: routes and dependencies."""
from __future__ import annotations

from .dependencies import get_workspace_identity, get_workspace_identity_optional

__all__ = ["get_workspace_identity", "get_workspace_identity_optional"]
