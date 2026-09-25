"""Plaintext and Markdown Exporter (Phase 10)."""
from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple
from .base_exporter import BaseExporter
from .schemas import MIME_TYPES


class TXTExporter(BaseExporter):
    """Generates structured Plaintext or Markdown files from deliverable content."""

    def __init__(self, is_markdown: bool = False):
        self.is_markdown = is_markdown

    async def export(
        self,
        deliverable: Dict[str, Any],
        uckr: Optional[Dict[str, Any]] = None,
        custom_title: Optional[str] = None,
    ) -> Tuple[bytes, str, str]:
        dtype = deliverable.get("type", "deliverable").replace("_", " ").title()
        title = custom_title or deliverable.get("title") or f"ContentForge {dtype}"
        content = deliverable.get("content", {})
        deliv_id = deliverable.get("deliverableId") or deliverable.get("id") or "export"

        lines = [
            f"CONTENTFORGE AI — {title.upper()}",
            "=" * len(f"CONTENTFORGE AI — {title.upper()}"),
            "",
        ]

        if isinstance(content, dict):
            for k, v in content.items():
                section_title = str(k).replace("_", " ").title()
                if self.is_markdown:
                    lines.append(f"## {section_title}")
                else:
                    lines.append(f"[{section_title}]")
                
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict):
                            for subk, subv in item.items():
                                lines.append(f"  • {subk}: {subv}")
                        else:
                            lines.append(f"  • {item}")
                elif isinstance(v, dict):
                    for subk, subv in v.items():
                        lines.append(f"  - {subk}: {subv}")
                else:
                    lines.append(f"{v}")
                lines.append("")
        elif isinstance(content, list):
            for item in content:
                lines.append(f"• {item}")
            lines.append("")
        else:
            lines.append(str(content))
            lines.append("")

        # Add UCKR Citation Traceability if available
        if uckr and uckr.get("facts"):
            facts = uckr.get("facts", [])
            lines.append("-" * 40)
            lines.append("GROUNDED CITATIONS & UCKR FACTS")
            lines.append("-" * 40)
            for f in facts[:10]:
                fid = f.get("factId") or f.get("id", "fact")
                fval = f.get("value") or f.get("text", "")
                conf = f.get("confidence", 0.95)
                lines.append(f"[{fid}] (Confidence: {conf*100:.0f}%) {fval}")
            lines.append("")

        text_output = "\n".join(lines)
        ext = "md" if self.is_markdown else "txt"
        mime = MIME_TYPES.get(ext, "text/plain")
        filename = f"{deliv_id}.{ext}"

        return text_output.encode("utf-8"), mime, filename
