"""Phase 7 RAG — Citation & Evidence Tracking.

Tracks source document chunks and graph evidence selected for context generation,
mapping numerical citation tags [1], [2] to exact document IDs, page numbers, and chunk IDs.
"""
from __future__ import annotations

import logging
from typing import List, Tuple

from .schemas import GraphEvidence, RetrievalResult, SourceCitation

log = logging.getLogger("gen-transform.rag.citations")


def _get(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


class CitationTracker:
    """Extracts and formats structured SourceCitation and GraphEvidence records."""

    def build_citations(
        self,
        context_candidates: List[RetrievalResult],
    ) -> Tuple[List[SourceCitation], List[GraphEvidence]]:
        """Extract vector source citations and graph evidence models from context items."""
        sources: List[SourceCitation] = []
        graph_evidence: List[GraphEvidence] = []

        citation_index = 1
        for cand in context_candidates:
            stype = _get(cand, "source_type")
            evidence = _get(cand, "evidence", {}) or {}
            metadata = _get(cand, "metadata", {}) or {}
            doc_id = _get(cand, "document_id") or evidence.get("document_id") or "doc"

            if stype == "vector":
                chunk_id = _get(cand, "source_id") or ""
                page = evidence.get("page") or metadata.get("page_number", 1)
                title = evidence.get("filename") or metadata.get("source_filename") or doc_id

                sources.append(
                    SourceCitation(
                        citation_id=str(citation_index),
                        document_id=doc_id,
                        chunk_id=chunk_id,
                        page=int(page) if page is not None else 1,
                        title=title,
                    )
                )
                citation_index += 1

            elif stype == "graph":
                src = str(metadata.get("source") or evidence.get("source") or "")
                rel = str(metadata.get("relation") or evidence.get("relation") or "")
                tgt = str(metadata.get("target") or evidence.get("target") or "")
                conf = float(_get(cand, "score", 0.0) or 0.0)
                ev_text = evidence.get("evidence_text") or metadata.get("evidence_text")

                graph_evidence.append(
                    GraphEvidence(
                        source=src,
                        relation=rel,
                        target=tgt,
                        document_id=doc_id,
                        confidence=conf,
                        evidence_text=ev_text,
                    )
                )

        log.debug("Citation tracker built %d vector citations, %d graph items", len(sources), len(graph_evidence))
        return sources, graph_evidence


__all__ = ["CitationTracker"]
