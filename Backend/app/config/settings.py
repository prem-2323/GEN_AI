"""Settings compatibility layer re-exporting from app.core.config."""
from __future__ import annotations

from ..core.config import Settings, get_settings

__all__ = ["Settings", "get_settings"]
