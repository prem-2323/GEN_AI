"""Phase 14 Provenance Engine — Provenance Builder.

Constructs structured OutputProvenance, ClaimProvenance, EvidenceRecord, and ProvenanceRecord
graph links from Phase 12 Transformation outputs, Phase 13 Validation results, and Phase 7 RAG contexts.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple
from .schemas import (
    ClaimProvenance,
    EvidenceRecord,
    OutputProvenance,
    ProvenanceMetadata,
    ProvenanceRecord,
    SourceTypeEnum,
)
from .hashing import ProvenanceHasher
from .resolver import EvidenceResolver

log = logging.getLogger("gen-transform.provenance.builder")


class ProvenanceBuilder:
    """Builder generating complete provenance records and directional lineage graphs."""

    def __init__(self, resolver: Optional[EvidenceResolver] = None) -> None:
        self.resolver: EvidenceResolver = resolver or EvidenceResolver()

    def build_output_provenance(
        self,
        output_id: str,
        content: str,
        claims_input: Optional[List[Dict[str, Any]]] = None,
        evidence_input: Optional[List[Dict[str, Any]]] = None,
        citations_input: Optional[List[Dict[str, Any]]] = None,
        validation_result: Optional[Dict[str, Any]] = None,
        pipeline_metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[OutputProvenance, List[ClaimProvenance], List[EvidenceRecord], List[ProvenanceRecord]]:
        """Construct full output provenance, claims, evidence, and directional links.

        Returns:
            Tuple of (OutputProvenance, List[ClaimProvenance], List[EvidenceRecord], List[ProvenanceRecord])
        """
        claims_input = claims_input or []
        evidence_input = evidence_input or []
        citations_input = citations_input or []
        pipeline_metadata = pipeline_metadata or {}

        # 1. Process evidence records
        evidence_records: List[EvidenceRecord] = []
        ev_id_map: Dict[str, EvidenceRecord] = {}
        document_ids_set = set()

        for raw_ev in evidence_input:
            rec = self.resolver.build_evidence_record(raw_ev)
            evidence_records.append(rec)
            ev_id_map[rec.evidence_id] = rec
            if rec.document_id:
                document_ids_set.add(rec.document_id)

        # 2. Extract metadata
        meta = ProvenanceMetadata(
            model_id=pipeline_metadata.get("model_id"),
            model_version=pipeline_metadata.get("model_version"),
            model_type=pipeline_metadata.get("model_type"),
            device=pipeline_metadata.get("device"),
            optimization_method=pipeline_metadata.get("optimization_method"),
            optimization_backend=pipeline_metadata.get("optimization_backend"),
            optimization_id=pipeline_metadata.get("optimization_id"),
            distillation_model=pipeline_metadata.get("distillation_model"),
            distillation_version=pipeline_metadata.get("distillation_version"),
            active_parameter_strategy=pipeline_metadata.get("active_parameter_strategy"),
            active_parameter_count=pipeline_metadata.get("active_parameter_count"),
            validation_id=validation_result.get("validation_id") if validation_result else None,
            transformation_type=pipeline_metadata.get("output_type", "SUMMARY"),
            language=pipeline_metadata.get("language", "en"),
        )

        val_id = validation_result.get("validation_id") if validation_result else None

        # 3. Build ClaimProvenance records and directional links
        claim_provenance_list: List[ClaimProvenance] = []
        links: List[ProvenanceRecord] = []

        for idx, raw_c in enumerate(claims_input):
            c_id = str(raw_c.get("claim_id") or f"claim-{output_id}-{idx+1}")
            c_text = str(raw_c.get("claim_text") or raw_c.get("text") or raw_c.get("subject", ""))

            c_ev_ids = [str(e) for e in raw_c.get("evidence_ids", [])]
            if not c_ev_ids and evidence_records:
                c_ev_ids = [e.evidence_id for e in evidence_records]

            # Aggregate pages, chunks, facts, entities, relations, docs
            c_doc_ids = set()
            c_pages = set()
            c_chunks = set()
            c_facts = set()
            c_entities = set()
            c_relations = set()

            for eid in c_ev_ids:
                erec = ev_id_map.get(eid) or self.resolver.resolve_evidence(eid)
                if erec:
                    if erec.document_id:
                        c_doc_ids.add(erec.document_id)
                        document_ids_set.add(erec.document_id)
                    if erec.page is not None:
                        c_pages.add(erec.page)
                    if erec.chunk_id:
                        c_chunks.add(erec.chunk_id)
                    if erec.fact_id:
                        c_facts.add(erec.fact_id)
                    if erec.entity_id:
                        c_entities.add(erec.entity_id)
                    if erec.relation_id:
                        c_relations.add(erec.relation_id)

                    # Link claim -> evidence
                    links.append(
                        ProvenanceRecord(
                            source_id=c_id,
                            target_id=eid,
                            source_type=SourceTypeEnum.TRANSFORMATION_CLAIM.value,
                            target_type=SourceTypeEnum.RAG_EVIDENCE.value,
                            relationship="SUPPORTED_BY",
                            document_id=erec.document_id,
                            page=erec.page,
                            chunk_id=erec.chunk_id,
                            evidence_id=eid,
                        )
                    )

                    # Link evidence -> chunk
                    if erec.chunk_id:
                        links.append(
                            ProvenanceRecord(
                                source_id=eid,
                                target_id=erec.chunk_id,
                                source_type=SourceTypeEnum.RAG_EVIDENCE.value,
                                target_type=SourceTypeEnum.CHUNK.value,
                                relationship="EXTRACTED_FROM_CHUNK",
                                document_id=erec.document_id,
                                page=erec.page,
                                chunk_id=erec.chunk_id,
                            )
                        )

                    # Link chunk -> document
                    if erec.document_id:
                        links.append(
                            ProvenanceRecord(
                                source_id=erec.chunk_id or eid,
                                target_id=erec.document_id,
                                source_type=SourceTypeEnum.CHUNK.value if erec.chunk_id else SourceTypeEnum.RAG_EVIDENCE.value,
                                target_type=SourceTypeEnum.DOCUMENT.value,
                                relationship="BELONGS_TO_DOCUMENT",
                                document_id=erec.document_id,
                                page=erec.page,
                            )
                        )

            c_prov = ClaimProvenance(
                claim_id=c_id,
                output_id=output_id,
                claim_text=c_text,
                evidence_ids=c_ev_ids,
                document_ids=list(c_doc_ids),
                page_numbers=sorted(list(c_pages)),
                chunk_ids=list(c_chunks),
                fact_ids=list(c_facts),
                entity_ids=list(c_entities),
                relation_ids=list(c_relations),
                citation_ids=[str(c.get("citation_id", "")) for c in citations_input if c.get("citation_id")],
                validation_id=val_id,
                status="RESOLVED" if c_ev_ids else "UNRESOLVED",
            )
            claim_provenance_list.append(c_prov)

            # Link output -> claim
            links.append(
                ProvenanceRecord(
                    source_id=output_id,
                    target_id=c_id,
                    source_type="OUTPUT",
                    target_type=SourceTypeEnum.TRANSFORMATION_CLAIM.value,
                    relationship="CONTAINS_CLAIM",
                )
            )

        citation_ids = [str(c.get("citation_id", "")) for c in citations_input if c.get("citation_id")]
        content_hash = ProvenanceHasher.generate_hash(content)

        output_prov = OutputProvenance(
            output_id=output_id,
            document_ids=list(document_ids_set),
            claim_ids=[cp.claim_id for cp in claim_provenance_list],
            evidence_ids=[er.evidence_id for er in evidence_records],
            citation_ids=citation_ids,
            validation_id=val_id,
            metadata=meta,
            transformation_metadata=pipeline_metadata,
            content_hash=content_hash,
        )

        return output_prov, claim_provenance_list, evidence_records, links


__all__ = ["ProvenanceBuilder"]
