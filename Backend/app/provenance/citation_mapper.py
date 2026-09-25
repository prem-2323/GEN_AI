"""Phase 14 Provenance Engine — Citation Mapper.

Maps inline citation tags ([1], [2], etc.) to supporting evidence, chunks, document pages,
and resolution statuses.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from .resolver import EvidenceResolver

log = logging.getLogger("gen-transform.provenance.citation_mapper")


class CitationMapper:
    """Mapper connecting citation tags to evidence records and document locations."""

    def __init__(self, resolver: Optional[EvidenceResolver] = None) -> None:
        self.resolver: EvidenceResolver = resolver or EvidenceResolver()

    def resolve_citation(self, citation_item: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve a single citation item dict to document locations.

        Returns structured dictionary containing citation_id, evidence_id, chunk_id, page,
        document_id, and resolution_status.
        """
        cit_id = str(citation_item.get("citation_id") or citation_item.get("id") or "")
        ev_id = str(citation_item.get("evidence_id") or "")

        if not cit_id:
            return {
                "citation_id": "UNKNOWN",
                "status": "CITATION_UNRESOLVED",
                "message": "Citation item lacks citation_id.",
            }

        # Normalize tag display (e.g., 1 -> [1])
        tag = cit_id if cit_id.startswith("[") else f"[{cit_id}]"

        loc = self.resolver.resolve_source_location(ev_id) if ev_id else {}

        doc_id = citation_item.get("document_id") or loc.get("document_id")
        chunk_id = citation_item.get("chunk_id") or loc.get("chunk_id")
        page = citation_item.get("page") or loc.get("page")
        section = citation_item.get("section") or loc.get("section")

        status = "RESOLVED" if (doc_id or ev_id) else "CITATION_UNRESOLVED"

        return {
            "citation_id": cit_id,
            "tag": tag,
            "status": status,
            "evidence_id": ev_id,
            "chunk_id": chunk_id,
            "document_id": doc_id,
            "page": page,
            "section": section,
        }

    def map_all_citations(self, citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Resolve list of citation dictionaries."""
        return [self.resolve_citation(c) for c in citations]


__all__ = ["CitationMapper"]
