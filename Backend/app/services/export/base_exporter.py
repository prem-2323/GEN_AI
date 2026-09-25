"""Base class for all file exporters (Phase 10)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple


class BaseExporter(ABC):
    """Abstract interface that all format exporters must implement."""

    @abstractmethod
    async def export(
        self,
        deliverable: Dict[str, Any],
        uckr: Optional[Dict[str, Any]] = None,
        custom_title: Optional[str] = None,
    ) -> Tuple[bytes, str, str]:
        """Convert deliverable into binary file data.
        
        Returns:
            Tuple[bytes, mime_type, filename]
        """
        pass
