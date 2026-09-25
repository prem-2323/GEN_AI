"""Phase 7 RAG — Prompt Builder.

Constructs grounded system instructions and user prompts for answer generation,
enforcing strict evidence citation and zero-hallucination constraints.
"""
from __future__ import annotations

import logging
from typing import Dict

log = logging.getLogger("gen-transform.rag.prompt_builder")

RAG_SYSTEM_PROMPT = """You are ContentForge AI's grounded Hybrid RAG Assistant.
Your task is to answer the user's question accurately using ONLY the provided Document Evidence and Graph Evidence.

STRICT INSTRUCTIONS:
1. Base your answer strictly on the supplied document text chunks and graph relationships.
2. Do NOT invent, assume, or extrapolate facts that are not directly supported by the context.
3. If the provided evidence is insufficient to answer the question, state clearly: "The retrieved evidence does not contain sufficient information to answer this question."
4. Include source citation markers [1], [2], etc., corresponding to the document source numbers when citing specific facts.
5. Keep your answer concise, objective, and professional.
"""


class PromptBuilder:
    """Builds prompt messages for LLM/generation model execution."""

    def build_prompt(self, query: str, context_text: str) -> Dict[str, str]:
        """Construct system and user messages."""
        user_message = (
            f"{context_text}\n\n"
            "INSTRUCTIONS:\n"
            "- Synthesize an accurate answer using the Document Evidence and Graph Evidence above.\n"
            "- Use source citation numbers like [1], [2] when referencing document evidence.\n"
            "- If evidence is missing or insufficient, state that evidence is insufficient.\n\n"
            f"QUESTION: {query}"
        )

        log.debug("Prompt builder constructed prompt for query '%s'", query[:40])
        return {
            "system": RAG_SYSTEM_PROMPT,
            "user": user_message,
        }


__all__ = ["PromptBuilder", "RAG_SYSTEM_PROMPT"]
