"""Export Manager — coordinates format exporters (Phase 10)."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

from .base_exporter import BaseExporter
from .txt_exporter import TXTExporter
from .docx_exporter import DOCXExporter
from .pdf_exporter import PDFExporter
from .pptx_exporter import PPTXExporter
from .audio_exporter import AudioExporter

log = logging.getLogger("gen-transform.export.manager")


class ExportManager:
    """Central registry and dispatcher for all export formats."""

    def __init__(self):
        self._exporters: Dict[str, BaseExporter] = {
            "txt": TXTExporter(is_markdown=False),
            "md": TXTExporter(is_markdown=True),
            "docx": DOCXExporter(),
            "pdf": PDFExporter(),
            "pptx": PPTXExporter(),
            "mp3": AudioExporter(),
        }

    def register_exporter(self, fmt: str, exporter: BaseExporter) -> None:
        self._exporters[fmt.lower()] = exporter

    async def generate_export(
        self,
        deliverable: Dict[str, Any],
        fmt: str,
        uckr: Optional[Dict[str, Any]] = None,
        custom_title: Optional[str] = None,
    ) -> Tuple[bytes, str, str]:
        """Convert deliverable to the requested file format.
        
        Returns: (file_bytes, mime_type, filename)
        """
        fmt_clean = fmt.lower().strip(".")
        exporter = self._exporters.get(fmt_clean)
        if not exporter:
            # Fallback to TXT if format not explicitly supported
            log.warning("Exporter not found for '%s', defaulting to TXT", fmt)
            exporter = self._exporters["txt"]

        return await exporter.export(deliverable, uckr=uckr, custom_title=custom_title)


_global_export_manager = ExportManager()


def get_export_manager() -> ExportManager:
    return _global_export_manager
