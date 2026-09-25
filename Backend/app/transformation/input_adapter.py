"""Phase 12 Transformation Engine — Input Adapter.

Normalizes input payloads from Phase 7 RAG, Phase 8 optimized evidence,
Phase 9 model layer, Phase 10 distilled model, or Phase 11 active parameters
into a standardized internal TransformationContext.
"""

from __future__ import annotations

import logging
from typing import List, Optional
from .schemas import (
    CitationReference,
    EntityItem,
    EvidenceItem,
    FactItem,
    RelationItem,
    TransformationContext,
    TransformationRequest,
)

log = logging.getLogger("gen-transform.transformation.input_adapter")


class TransformationInputAdapter:
    """Adapter normalizing heterogeneous inputs into TransformationContext."""

    def adapt(self, request: TransformationRequest) -> TransformationContext:
        """Convert TransformationRequest to standardized TransformationContext."""
        evidence_items: List[EvidenceItem] = list(request.evidence_items)
        citations: List[CitationReference] = []
        facts: List[FactItem] = []
        entities: List[EntityItem] = []
        relations: List[RelationItem] = []
        graph_evidence: List[dict] = []

        # 1. Compile source content
        compiled_parts: List[str] = []
        if request.source_text and request.source_text.strip():
            compiled_parts.append(request.source_text.strip())

        for idx, item in enumerate(evidence_items, start=1):
            cit_id = f"[{idx}]"
            citations.append(
                CitationReference(
                    citation_id=cit_id,
                    evidence_id=item.evidence_id,
                    document_id=item.document_id,
                    page=item.page,
                    chunk_id=item.chunk_id,
                    text_snippet=item.content[:100] if item.content else None,
                )
            )
            # Compile evidence text if source_text is empty or to complement it
            if not request.source_text:
                compiled_parts.append(f"Evidence {cit_id}: {item.content.strip()}")

            # Extract facts/entities/relations from metadata if present
            if item.metadata:
                if "graph_data" in item.metadata:
                    graph_evidence.append(item.metadata["graph_data"])
                if "facts" in item.metadata and isinstance(item.metadata["facts"], list):
                    for f in item.metadata["facts"]:
                        if isinstance(f, dict):
                            facts.append(
                                FactItem(
                                    subject=f.get("subject", ""),
                                    predicate=f.get("predicate", ""),
                                    object_val=f.get("object", f.get("object_val", "")),
                                    confidence=float(f.get("confidence", 1.0)),
                                )
                            )

        source_content = "\n\n".join(compiled_parts).strip()
        insufficient_evidence = False

        if not source_content and not evidence_items:
            insufficient_evidence = True
            log.warning("TransformationRequest contains no source_text and no evidence_items.")

        context = TransformationContext(
            document_ids=list(request.document_ids),
            source_content=source_content,
            evidence_items=evidence_items,
            graph_evidence=graph_evidence,
            facts=facts,
            entities=entities,
            relations=relations,
            citations=citations,
            requested_output=request.output_type,
            audience=request.audience,
            tone=request.tone,
            language=request.language,
            target_language=request.target_language,
            detail_level=request.detail_level,
            objective=request.objective,
            instructions=request.instructions,
            model_metadata={
                "model_id": request.model_id or "default",
                "model_type": request.model_type,
            },
            insufficient_evidence=insufficient_evidence,
        )

        return context


__all__ = ["TransformationInputAdapter"]
