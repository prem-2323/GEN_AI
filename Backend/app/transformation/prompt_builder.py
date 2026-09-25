"""Phase 12 Transformation Engine — Prompt Builder.

Constructs profile-driven generation prompts incorporating strict factual preservation
rules, expected section structures, target audience, tone, language, and citation controls.
"""

from __future__ import annotations

import logging
from typing import Optional
from .schemas import TransformationContext, TransformationProfile

log = logging.getLogger("gen-transform.transformation.prompt_builder")


class TransformationPromptBuilder:
    """Builder generating profile-driven prompts with factual preservation constraints."""

    def build_prompt(
        self, context: TransformationContext, profile: TransformationProfile
    ) -> str:
        """Construct structured prompt for model inference."""
        lines = []

        # 1. System Role & Task Instructions
        lines.append(f"### SYSTEM ROLE: Knowledge Transformation System")
        lines.append(f"TASK: Transform the supplied source knowledge into a '{profile.name}' ({profile.output_type}).")
        lines.append(f"PURPOSE: {profile.purpose}")

        # 2. Audience, Tone, Language & Formatting Parameters
        lines.append("\n### PARAMETERS:")
        lines.append(f"- Output Type: {profile.output_type}")
        lines.append(f"- Target Audience: {context.audience}")
        lines.append(f"- Presentation Tone: {context.tone}")
        lines.append(f"- Source Language: {context.language}")
        if context.target_language:
            lines.append(f"- Target Language: {context.target_language}")
        lines.append(f"- Detail Level: {context.detail_level}")
        lines.append(f"- Target Length: {profile.target_length}")
        if context.objective:
            lines.append(f"- Strategic Objective: {context.objective}")
        if context.instructions:
            lines.append(f"- Custom User Instructions: {context.instructions}")

        # 3. Expected Output Structure
        lines.append("\n### MANDATORY OUTPUT STRUCTURE:")
        lines.append(f"Your output MUST contain the following sections formatted with clear Markdown headers:")
        for sec in profile.expected_structure:
            lines.append(f"  ## {sec.replace('_', ' ').title()}")

        # 4. Critical Fact Preservation & Citation Rules
        lines.append("\n### CRITICAL FACT PRESERVATION & SAFETY RULES:")
        lines.append("1. ZERO HALLUCINATION: Rely STRICTLY on the supplied source evidence below. Do NOT invent claims.")
        lines.append("2. PRESERVE NUMERICAL VALUES: Exact numbers, percentages, quantities, and statistics MUST be preserved unchanged.")
        lines.append("3. PRESERVE DATES & TIMES: Calendar dates, years, and timestamps MUST be preserved unchanged (e.g. 2026-01-10 stays 2026-01-10).")
        lines.append("4. PRESERVE ENTITIES: Product names, organizational names, proper nouns, and locations MUST NOT be altered.")
        lines.append("5. CITATION MATCHING: Use ONLY the valid inline citation IDs provided in the evidence below (e.g., [1], [2]).")
        lines.append("   DO NOT invent or fabricate nonexistent citation IDs (such as [99] or unsupported references).")
        lines.append("6. INSUFFICIENT EVIDENCE: If the evidence does not contain sufficient facts to fulfill a required section, state '[Insufficient evidence for this section]' rather than inventing details.")

        # 5. Citation Details & Source Evidence
        lines.append("\n### SUPPLIED SOURCE EVIDENCE:")
        if context.citations:
            for cit in context.citations:
                lines.append(f"Citation {cit.citation_id} (Evidence ID: {cit.evidence_id}):")
                if cit.text_snippet:
                    lines.append(f"  Snippet: {cit.text_snippet}")
        lines.append("\n--- BEGIN SOURCE CONTENT ---")
        lines.append(context.source_content if context.source_content else "[No source content available]")
        lines.append("--- END SOURCE CONTENT ---")

        lines.append("\nGenerate the completed transformation deliverable now following all structural and factual preservation rules above:")

        return "\n".join(lines)


__all__ = ["TransformationPromptBuilder"]
