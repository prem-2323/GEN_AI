"""Phase 12 Transformation Engine — Output Parser.

Parses generated output, validates section structure, verifies inline citations,
detects hallucinated citation IDs, and constructs StructuredContent models.
"""

from __future__ import annotations

import re
import logging
from typing import List, Set, Tuple
from .schemas import (
    CitationReference,
    StructuredContent,
    StructuredSection,
    TransformationContext,
    TransformationProfile,
)

log = logging.getLogger("gen-transform.transformation.output_parser")


class TransformationOutputParser:
    """Parser validating model output, extracting citations, and enforcing structure."""

    def parse(
        self,
        raw_output: str,
        context: TransformationContext,
        profile: TransformationProfile,
    ) -> Tuple[StructuredContent, List[str], List[CitationReference]]:
        """Parse raw model output text into StructuredContent.

        Returns:
            Tuple of (StructuredContent, warnings_list, valid_citations_list)
        """
        warnings: List[str] = []
        valid_citation_ids: Set[str] = {c.citation_id for c in context.citations}
        matched_citations: List[CitationReference] = []

        # 1. Detect all inline citation IDs using regex (e.g., [1], [2], [99])
        found_citation_tags = re.findall(r"\[\d+\]", raw_output)
        found_set = set(found_citation_tags)

        # 2. Check for invalid/hallucinated citation IDs
        sanitized_output = raw_output
        for tag in found_set:
            if valid_citation_ids and tag not in valid_citation_ids:
                warnings.append(f"Hallucinated citation ID {tag} detected and flagged.")
                log.warning("Output parser detected hallucinated citation %s not in context.", tag)

        # Collect valid matching citation objects
        for c in context.citations:
            if c.citation_id in found_set:
                matched_citations.append(c)

        # 3. Parse output sections based on headers or markdown headings
        sections: List[StructuredSection] = []
        raw_lines = raw_output.split("\n")

        current_title = ""
        current_section_name = "general"
        current_section_lines: List[str] = []

        for line in raw_lines:
            header_match = re.match(r"^#{1,3}\s+(.+)$", line.strip())
            if header_match:
                header_text = header_match.group(1).strip()
                if not current_title:
                    current_title = header_text

                # Save previous section if exists
                if current_section_lines:
                    sec_body = "\n".join(current_section_lines).strip()
                    sec_cits = re.findall(r"\[\d+\]", sec_body)
                    sec_evid_ids = [
                        c.evidence_id for c in context.citations if c.citation_id in sec_cits
                    ]
                    sections.append(
                        StructuredSection(
                            section_name=current_section_name,
                            title=current_section_name.replace("_", " ").title(),
                            content=sec_body,
                            evidence_ids=list(set(sec_evid_ids)),
                            citations=list(set(sec_cits)),
                        )
                    )
                    current_section_lines = []

                current_section_name = header_text.lower().replace(" ", "_")
            else:
                current_section_lines.append(line)

        # Append final trailing section
        if current_section_lines:
            sec_body = "\n".join(current_section_lines).strip()
            sec_cits = re.findall(r"\[\d+\]", sec_body)
            sec_evid_ids = [
                c.evidence_id for c in context.citations if c.citation_id in sec_cits
            ]
            sections.append(
                StructuredSection(
                    section_name=current_section_name,
                    title=current_section_name.replace("_", " ").title(),
                    content=sec_body,
                    evidence_ids=list(set(sec_evid_ids)),
                    citations=list(set(sec_cits)),
                )
            )

        # If no markdown sections were parsed, wrap entire raw_output in a single main section
        if not sections:
            sec_cits = re.findall(r"\[\d+\]", raw_output)
            sec_evid_ids = [
                c.evidence_id for c in context.citations if c.citation_id in sec_cits
            ]
            sections.append(
                StructuredSection(
                    section_name="content",
                    title=profile.name,
                    content=raw_output.strip(),
                    evidence_ids=list(set(sec_evid_ids)),
                    citations=list(set(sec_cits)),
                )
            )

        structured_content = StructuredContent(
            title=current_title or f"{profile.name} Deliverable",
            summary=sections[0].content[:200] if sections else "",
            sections=sections,
            metadata={
                "output_type": profile.output_type,
                "sections_count": len(sections),
                "citations_found": len(found_set),
            },
        )

        return structured_content, warnings, matched_citations


__all__ = ["TransformationOutputParser"]
