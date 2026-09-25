"""Phase 14 Provenance Engine — Lineage Service.

Constructs forward (Output → Claim → Evidence → Document) and reverse
(Document → Evidence → Claim → Output) lineage trees for artifact traceability.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from .schemas import LineageNode, LineageTree, SourceTypeEnum
from .repository import ProvenanceRepository
from .resolver import EvidenceResolver

log = logging.getLogger("gen-transform.provenance.lineage")


class LineageService:
    """Service traversing provenance graphs in forward and reverse directions."""

    def __init__(
        self,
        repository: Optional[ProvenanceRepository] = None,
        resolver: Optional[EvidenceResolver] = None,
    ) -> None:
        self.repository = repository or ProvenanceRepository()
        self.resolver = resolver or EvidenceResolver()

    def get_forward_lineage(self, output_id: str) -> LineageTree:
        """Construct forward lineage tree starting from output_id down to original document."""
        output = self.repository.get_output(output_id)
        if not output:
            root = LineageNode(
                node_id=output_id,
                node_type="OUTPUT",
                label=f"Output '{output_id}' (NOT_FOUND)",
            )
            return LineageTree(
                root_id=output_id,
                direction="FORWARD",
                tree=root,
                total_nodes=1,
                depth=1,
                completeness_score=0.0,
            )

        claims = self.repository.get_claims_for_output(output_id)
        claim_nodes: List[LineageNode] = []
        total_nodes = 1  # root
        max_depth = 2
        resolved_claims = 0

        for c in claims:
            ev_nodes: List[LineageNode] = []
            if c.status == "RESOLVED":
                resolved_claims += 1

            for eid in c.evidence_ids:
                erec = self.repository.get_evidence(eid) or self.resolver.resolve_evidence(eid)
                chunk_node = None
                doc_node = None

                if erec:
                    if erec.chunk_id:
                        total_nodes += 1
                        chunk_node = LineageNode(
                            node_id=erec.chunk_id,
                            node_type=SourceTypeEnum.CHUNK.value,
                            label=f"Chunk {erec.chunk_id}",
                            location={"chunk_id": erec.chunk_id, "page": erec.page},
                        )

                    doc_node = LineageNode(
                        node_id=erec.document_id,
                        node_type=SourceTypeEnum.DOCUMENT.value,
                        label=f"Document '{erec.document_id}'",
                        location={
                            "document_id": erec.document_id,
                            "page": erec.page,
                            "section": erec.section,
                            "text_span": erec.text_span,
                            "fact_id": erec.fact_id,
                            "relation_id": erec.relation_id,
                        },
                    )
                    total_nodes += 1

                    ev_children = []
                    if chunk_node:
                        chunk_node.children.append(doc_node)
                        ev_children.append(chunk_node)
                    else:
                        ev_children.append(doc_node)

                    ev_node = LineageNode(
                        node_id=eid,
                        node_type=SourceTypeEnum.RAG_EVIDENCE.value,
                        label=f"Evidence {eid}",
                        location={"page": erec.page, "section": erec.section},
                        metadata={"content_hash": erec.content_hash, "content": erec.content[:100]},
                        children=ev_children,
                    )
                    ev_nodes.append(ev_node)
                    total_nodes += 1

            c_node = LineageNode(
                node_id=c.claim_id,
                node_type=SourceTypeEnum.TRANSFORMATION_CLAIM.value,
                label=f"Claim: '{c.claim_text[:60]}'",
                metadata={"validation_id": c.validation_id, "status": c.status},
                children=ev_nodes,
            )
            claim_nodes.append(c_node)
            total_nodes += 1

        root = LineageNode(
            node_id=output_id,
            node_type="OUTPUT",
            label=f"Deliverable Output '{output_id}'",
            metadata={
                "validation_id": output.validation_id,
                "content_hash": output.content_hash,
                "documents": output.document_ids,
            },
            children=claim_nodes,
        )

        completeness = resolved_claims / len(claims) if claims else 1.0

        return LineageTree(
            root_id=output_id,
            direction="FORWARD",
            tree=root,
            total_nodes=total_nodes,
            depth=4,
            completeness_score=completeness,
        )

    def get_reverse_lineage(self, document_id: str) -> LineageTree:
        """Construct reverse lineage tree starting from document_id up to generated outputs."""
        all_evidence = [e for e in self.repository.get_all_evidence() if e.document_id == document_id]
        all_outputs = [o for o in self.repository.get_all_outputs() if document_id in o.document_ids]

        ev_nodes: List[LineageNode] = []
        total_nodes = 1

        for ev in all_evidence:
            matching_claims = [
                c for c in self.repository._claims.values() if ev.evidence_id in c.evidence_ids
            ]
            c_nodes: List[LineageNode] = []
            for c in matching_claims:
                o_nodes = [
                    LineageNode(
                        node_id=c.output_id,
                        node_type="OUTPUT",
                        label=f"Output {c.output_id}",
                    )
                ]
                total_nodes += 1
                c_node = LineageNode(
                    node_id=c.claim_id,
                    node_type=SourceTypeEnum.TRANSFORMATION_CLAIM.value,
                    label=f"Claim '{c.claim_text[:60]}'",
                    children=o_nodes,
                )
                c_nodes.append(c_node)
                total_nodes += 1

            ev_node = LineageNode(
                node_id=ev.evidence_id,
                node_type=SourceTypeEnum.RAG_EVIDENCE.value,
                label=f"Evidence {ev.evidence_id} (Page {ev.page})",
                children=c_nodes,
            )
            ev_nodes.append(ev_node)
            total_nodes += 1

        root = LineageNode(
            node_id=document_id,
            node_type=SourceTypeEnum.DOCUMENT.value,
            label=f"Document '{document_id}'",
            metadata={"evidence_count": len(all_evidence), "outputs_count": len(all_outputs)},
            children=ev_nodes,
        )

        return LineageTree(
            root_id=document_id,
            direction="REVERSE",
            tree=root,
            total_nodes=total_nodes,
            depth=4,
            completeness_score=1.0,
        )


__all__ = ["LineageService"]
