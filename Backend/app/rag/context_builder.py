"""Phase 7 RAG — Context Builder.

Assembles retrieved vector chunks and graph relationships into a clean, ordered,
budget-constrained context payload for the answer generation model.
"""
from __future__ import annotations

import logging
from typing import List, Tuple

from .schemas import RetrievalResult

log = logging.getLogger("gen-transform.rag.context_builder")

DEFAULT_MAX_CONTEXT_CHUNKS = 5
DEFAULT_MAX_GRAPH_RESULTS = 10
DEFAULT_MAX_CONTEXT_TOKENS = 3000  # Approx ~12,000 characters


class ContextBuilder:
    """Enforces token budgets and formats vector + graph evidence into structured context."""

    def __init__(
        self,
        max_chunks: int = DEFAULT_MAX_CONTEXT_CHUNKS,
        max_graph: int = DEFAULT_MAX_GRAPH_RESULTS,
        max_tokens: int = DEFAULT_MAX_CONTEXT_TOKENS,
    ) -> None:
        self.max_chunks = max_chunks
        self.max_graph = max_graph
        self.max_tokens = max_tokens

    def build_context(
        self,
        query: str,
        candidates: List[RetrievalResult],
    ) -> Tuple[str, List[RetrievalResult]]:
        """Filter candidates by budget and build structured context text for generation."""
        vector_candidates = [c for c in candidates if c.source_type == "vector"][: self.max_chunks]
        graph_candidates = [c for c in candidates if c.source_type == "graph"][: self.max_graph]

        selected_candidates: List[RetrievalResult] = []
        doc_evidence_lines: List[str] = []
        graph_evidence_lines: List[str] = []
        source_info_lines: List[str] = []

        citation_index = 1
        current_char_count = 0
        max_char_limit = self.max_tokens * 4

        # 1. Format Document Vector Evidence
        for cand in vector_candidates:
            doc_id = cand.document_id or cand.evidence.get("document_id") or "doc"
            page = cand.evidence.get("page") or cand.metadata.get("page_number", 1)
            filename = cand.evidence.get("filename") or cand.metadata.get("source_filename") or doc_id

            block = f"SOURCE [{citation_index}]\nDocument: {filename}\nPage: {page}\nText: {cand.text}\n"
            if current_char_count + len(block) > max_char_limit:
                break

            doc_evidence_lines.append(block)
            source_info_lines.append(f"[{citation_index}] Document '{filename}' (ID: {doc_id}), Page {page}")
            selected_candidates.append(cand)
            citation_index += 1
            current_char_count += len(block)

        # 2. Format Graph Relationship Evidence
        for cand in graph_candidates:
            src = cand.metadata.get("source") or cand.evidence.get("source", "")
            rel = cand.metadata.get("relation") or cand.evidence.get("relation", "")
            tgt = cand.metadata.get("target") or cand.evidence.get("target", "")
            ev_text = cand.evidence.get("evidence_text", "")

            line = f"- {src} ──[{rel}]──> {tgt}"
            if ev_text:
                line += f" (Evidence: '{ev_text}')"

            if current_char_count + len(line) > max_char_limit:
                break

            graph_evidence_lines.append(line)
            selected_candidates.append(cand)
            current_char_count += len(line)

        # 3. Assemble Structured Prompt Context
        context_parts: List[str] = []

        context_parts.append(f"USER QUESTION:\n{query.strip()}\n")

        if doc_evidence_lines:
            context_parts.append("DOCUMENT EVIDENCE:\n" + "-----------------\n" + "\n".join(doc_evidence_lines))
        else:
            context_parts.append("DOCUMENT EVIDENCE:\n-----------------\nNo direct document vector evidence found.\n")

        if graph_evidence_lines:
            context_parts.append("\nGRAPH EVIDENCE:\n---------------\n" + "\n".join(graph_evidence_lines))
        else:
            context_parts.append("\nGRAPH EVIDENCE:\n---------------\nNo graph relationship evidence found.\n")

        if source_info_lines:
            context_parts.append("\nSOURCE INFORMATION:\n------------------\n" + "\n".join(source_info_lines))

        full_context_text = "\n".join(context_parts)

        log.debug(
            "Context builder constructed context with %d vector items, %d graph items (%d chars)",
            len(doc_evidence_lines),
            len(graph_evidence_lines),
            len(full_context_text),
        )

        return full_context_text, selected_candidates


__all__ = ["ContextBuilder"]
