"""API dependencies for the shared local workspace."""
from __future__ import annotations

from typing import Optional


async def get_workspace_identity() -> dict:
    """Return the shared local workspace identity; no authentication is used."""
    return {"uid": "local-workspace", "email": "", "dev": True}


async def get_workspace_identity_optional() -> Optional[dict]:
    """Return the local workspace identity for public routes."""
    return {"uid": "local-workspace", "email": "", "dev": True}
