"""Auth compatibility layer re-exporting dependencies from app.api.dependencies."""
from __future__ import annotations

from .api.dependencies import (
    get_current_user,
    get_current_user_optional,
    _dev_user,
    _decode_unverified_jwt,
)

__all__ = [
    "get_current_user",
    "get_current_user_optional",
    "_dev_user",
    "_decode_unverified_jwt",
]
