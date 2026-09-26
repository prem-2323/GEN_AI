"""Phase 7 Grounded RAG Context Builder.

Formats QUBO-selected evidence candidates into structured [E1], [E2]... blocks for the QLoRA student prompt,
preserving document ID, page numbers, chunk IDs, and verbatim source text.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def build_grounded_context(
    selected_candidates: List[Dict[str, Any]]
) -> Tuple[str, List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """Build structured grounded context string and evidence manifest from selected evidence candidates.

    Returns:
      - formatted_context: Context string formatted as [E1], [E2]... blocks
      - evidence_manifest: List of structured evidence objects
      - citations_map: Map of evidence_id -> metadata
    """
    if not selected_candidates:
        return (
            "NO_EVIDENCE_PROVIDED: No relevant source evidence was retrieved or selected.",
            [],
            {},
        )

    vector_blocks = []
    graph_blocks = []
    evidence_manifest = []
    citations_map = {}

    for idx, item in enumerate(selected_candidates, start=1):
        evidence_id = f"E{idx}"
        doc_id = str(item.get("document_id") or "doc_unknown")
        chunk_id = str(item.get("chunk_id") or item.get("source_id") or item.get("id") or f"chunk_{idx}")
        page_num = int(item.get("page_number") or item.get("page") or 1)
        source = str(item.get("source") or item.get("retrieval_method") or item.get("source_type") or "hybrid")
        text = str(item.get("text") or "").strip()
        rrf_score = float(item.get("rrf_score") or item.get("score") or 0.0)
        qubo_sel = bool(item.get("selected_by_qubo", True))
        stype = item.get("source_type") or ("graph" if "--[" in text or "rel_" in str(chunk_id) or str(chunk_id).startswith("r") else "vector")

        block = (
            f"[{evidence_id}]\n"
            f"Document: {doc_id}\n"
            f"Page: {page_num}\n"
            f"Chunk: {chunk_id}\n"
            f"Source: {source}\n"
            f"Text: {text}"
        )

        if stype == "graph":
            graph_blocks.append(block)
        else:
            vector_blocks.append(block)

        evidence_obj = {
            "evidence_id": evidence_id,
            "document_id": doc_id,
            "chunk_id": chunk_id,
            "page_number": page_num,
            "source": source,
            "text": text,
            "rrf_score": round(rrf_score, 6),
            "qubo_selected": qubo_sel,
            "source_type": stype,
        }
        evidence_manifest.append(evidence_obj)
        citations_map[evidence_id] = evidence_obj

    sections = ["SOURCE INFORMATION: Grounded Context"]
    sections.append("DOCUMENT EVIDENCE:\n" + ("\n\n".join(vector_blocks) if vector_blocks else "None"))
    sections.append("GRAPH EVIDENCE:\n" + ("\n\n".join(graph_blocks) if graph_blocks else "None"))

    formatted_context = "\n\n".join(sections)
    return formatted_context, evidence_manifest, citations_map


def build_strict_grounded_prompt(question: str, formatted_context: str) -> str:
    """Construct strict anti-hallucination grounded prompt for QLoRA student model."""
    prompt = (
        "SYSTEM:\n"
        "You are a grounded document question-answering assistant.\n\n"
        "RULES:\n"
        "1. Use ONLY the supplied evidence below to answer the question.\n"
        "2. Do NOT invent facts or use outside knowledge.\n"
        "3. Preserve all numbers, percentages, precision metrics, and units EXACTLY as written in the evidence.\n"
        "4. If the supplied evidence does NOT contain the information needed to answer, explicitly state: 'The supplied evidence is insufficient to answer this query.'\n"
        "5. Cite the evidence IDs used (e.g. [E1], [E2]) in your answer.\n\n"
        f"SUPPLIED EVIDENCE:\n\n"
        f"{formatted_context}\n\n"
        f"QUESTION: {question}\n\n"
        "ANSWER:"
    )
    return prompt


class ContextBuilder:
    """Wrapper class for building grounded context for backward compatibility."""

    def __init__(
        self,
        max_chunks: int = 5,
        max_graph: int = 5,
        max_tokens: int = 2000,
        **kwargs: Any,
    ):
        self.max_chunks = max_chunks
        self.max_graph = max_graph
        self.max_tokens = max_tokens

    def build_context(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        candidates: List[Any] = []
        query: Optional[str] = None

        for arg in args:
            if isinstance(arg, str):
                query = arg
            elif isinstance(arg, list):
                candidates = arg

        if "candidates" in kwargs and kwargs["candidates"] is not None:
            candidates = kwargs["candidates"]
        elif "selected_candidates" in kwargs and kwargs["selected_candidates"] is not None:
            candidates = kwargs["selected_candidates"]

        if "query" in kwargs and kwargs["query"] is not None:
            query = kwargs["query"]

        converted = []
        for c in candidates:
            if hasattr(c, "model_dump"):
                converted.append(c.model_dump())
            elif hasattr(c, "__dict__") and not isinstance(c, dict):
                converted.append(c.__dict__)
            else:
                converted.append(c)
        ctx_text, manifest, _ = build_grounded_context(converted)
        return ctx_text, manifest

    def build_prompt(self, question: str, formatted_context: str) -> str:
        return build_strict_grounded_prompt(question, formatted_context)


__all__ = [
    "build_grounded_context",
    "build_strict_grounded_prompt",
    "ContextBuilder",
]
