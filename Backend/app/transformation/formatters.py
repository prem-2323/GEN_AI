"""Phase 12 Transformation Engine — Formatters.

Converts TransformationResponse and StructuredContent into plain text,
Markdown, or structured JSON representations.
"""

from __future__ import annotations

import json
from typing import Any, Dict
from .schemas import TransformationResponse


class TransformationFormatter:
    """Formatter converting transformation outputs to target formats."""

    @staticmethod
    def to_markdown(response: TransformationResponse) -> str:
        """Format transformation response as clean Markdown."""
        lines = [f"# {response.title}", ""]

        if response.structured_content and response.structured_content.sections:
            for sec in response.structured_content.sections:
                lines.append(f"## {sec.title}")
                lines.append(sec.content)
                lines.append("")
        else:
            lines.append(response.content)

        if response.citations:
            lines.append("## References & Citations")
            for cit in response.citations:
                snip = f" — '{cit.text_snippet}'" if cit.text_snippet else ""
                lines.append(f"- **{cit.citation_id}**: Evidence ID `{cit.evidence_id}`{snip}")

        return "\n".join(lines).strip()

    @staticmethod
    def to_plain_text(response: TransformationResponse) -> str:
        """Format transformation response as plain text."""
        lines = [response.title.upper(), "=" * len(response.title), ""]

        if response.structured_content and response.structured_content.sections:
            for sec in response.structured_content.sections:
                lines.append(sec.title)
                lines.append("-" * len(sec.title))
                lines.append(sec.content)
                lines.append("")
        else:
            lines.append(response.content)

        return "\n".join(lines).strip()

    @staticmethod
    def to_json(response: TransformationResponse) -> str:
        """Format transformation response as JSON string."""
        return response.model_dump_json(indent=2)


__all__ = ["TransformationFormatter"]
