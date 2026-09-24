"""Helper utilities."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict

_ID_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_valid_id(val: str) -> bool:
    return bool(val and len(val) <= 128 and _ID_RE.match(val))


def sanitize_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}
