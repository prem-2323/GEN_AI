"""Phase 14 Provenance Engine — Evidence Resolver.

Resolves evidence identifiers to exact source locations (document ID, page number, section,
text span, vector chunk, graph node/relation, DocLink fact/entity).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from .schemas import EvidenceRecord, SourceTypeEnum
from .hashing import ProvenanceHasher

log = logging.getLogger("gen-transform.provenance.resolver")


class EvidenceResolver:
    """Resolver auditing evidence items and expanding detailed source locations."""

    def __init__(self, evidence_store: Optional[Dict[str, EvidenceRecord]] = None) -> None:
        self.evidence_store: Dict[str, EvidenceRecord] = evidence_store or {}

    def register_evidence(self, evidence: EvidenceRecord) -> None:
        """Register or update an EvidenceRecord in memory."""
        if not evidence.content_hash and evidence.content:
            evidence.content_hash = ProvenanceHasher.generate_hash(evidence.content)
        self.evidence_store[evidence.evidence_id] = evidence

    def resolve_evidence(self, evidence_id: str) -> Optional[EvidenceRecord]:
        """Lookup EvidenceRecord by evidence_id. Returns None if unresolved."""
        return self.evidence_store.get(evidence_id)

    def build_evidence_record(self, raw_item: Dict[str, Any]) -> EvidenceRecord:
        """Construct a detailed EvidenceRecord from a raw evidence dict (from RAG/Phase 7/12/13)."""
        ev_id = str(raw_item.get("evidence_id") or raw_item.get("id") or "")
        if not ev_id:
            ev_id = f"ev-{ProvenanceHasher.generate_hash(raw_item)[:12]}"

        doc_id = str(raw_item.get("document_id") or raw_item.get("doc_id") or "UNKNOWN_DOC")
        page = raw_item.get("page") or raw_item.get("page_number")
        if isinstance(page, str) and page.isdigit():
            page = int(page)
        elif not isinstance(page, int):
            page = None

        section = raw_item.get("section") or raw_item.get("section_name")
        text_span = raw_item.get("text_span") or raw_item.get("span")
        chunk_id = raw_item.get("chunk_id")
        fact_id = raw_item.get("fact_id")
        entity_id = raw_item.get("entity_id")
        relation_id = raw_item.get("relation_id")

        content = raw_item.get("content") or raw_item.get("text") or ""
        content_hash = raw_item.get("content_hash") or ProvenanceHasher.generate_hash(content)

        source_type = raw_item.get("source_type") or SourceTypeEnum.RAG_EVIDENCE.value

        record = EvidenceRecord(
            evidence_id=ev_id,
            document_id=doc_id,
            source_type=source_type,
            page=page,
            section=str(section) if section else None,
            text_span=str(text_span) if text_span else None,
            chunk_id=str(chunk_id) if chunk_id else None,
            fact_id=str(fact_id) if fact_id else None,
            entity_id=str(entity_id) if entity_id else None,
            relation_id=str(relation_id) if relation_id else None,
            content_hash=content_hash,
            content=str(content),
            metadata=raw_item.get("metadata", {}),
        )

        self.register_evidence(record)
        return record

    def resolve_source_location(self, evidence_id: str) -> Dict[str, Any]:
        """Return structured location map for an evidence ID, or status UNRESOLVED."""
        record = self.resolve_evidence(evidence_id)
        if not record:
            return {
                "evidence_id": evidence_id,
                "status": "EVIDENCE_NOT_FOUND",
                "message": f"Evidence ID '{evidence_id}' could not be resolved to ground truth.",
            }

        return {
            "evidence_id": record.evidence_id,
            "status": "RESOLVED",
            "document_id": record.document_id,
            "page": record.page,
            "section": record.section,
            "text_span": record.text_span,
            "chunk_id": record.chunk_id,
            "fact_id": record.fact_id,
            "entity_id": record.entity_id,
            "relation_id": record.relation_id,
            "content_hash": record.content_hash,
        }


__all__ = ["EvidenceResolver"]
