"""Phase 7 RAG — Citation & Evidence Tracking.

Tracks source document chunks and graph evidence selected for context generation,
mapping numerical citation tags [1], [2] to exact document IDs, page numbers, and chunk IDs.
"""
from __future__ import annotations

import logging
from typing import List, Tuple

from .schemas import GraphEvidence, RetrievalResult, SourceCitation

log = logging.getLogger("gen-transform.rag.citations")


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
            if cand.source_type == "vector":
                doc_id = cand.document_id or cand.evidence.get("document_id") or "doc"
                chunk_id = cand.source_id
                page = cand.evidence.get("page") or cand.metadata.get("page_number", 1)
                title = cand.evidence.get("filename") or cand.metadata.get("source_filename") or doc_id

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

            elif cand.source_type == "graph":
                src = str(cand.metadata.get("source") or cand.evidence.get("source") or "")
                rel = str(cand.metadata.get("relation") or cand.evidence.get("relation") or "")
                tgt = str(cand.metadata.get("target") or cand.evidence.get("target") or "")
                doc_id = cand.document_id or cand.evidence.get("document_id")
                conf = float(cand.score)
                ev_text = cand.evidence.get("evidence_text") or cand.metadata.get("evidence_text")

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
