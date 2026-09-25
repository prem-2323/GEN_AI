"""DocLink Service — Orchestrates complete DocLink pipeline (Phase 4).

Architecture::

    ExtractedDocument / Text
           ↓
    DocLink Engine
       ├── Chunking (Logical Sections / Pages)
       ├── Entity Extractor  (LLM + Deterministic)
       ├── Fact Extractor    (LLM + Deterministic)
       └── Relation Extractor (LLM + Deterministic)
           ↓
    Normalization & Deduplication
       ├── Entity Clustering & Canonical Naming
       ├── Fact & Relation Re-indexing
       └── Cross-Chunk Coreference Resolution
           ↓
    Evidence & Source Tracking (SourceSpan)
           ↓
    Validation (Pydantic + Strict Rule Check)
           ↓
    UCKR Representation (UCKR-compatible Projection)
           ↓
    Graph-Ready Structure (Nodes + Edges, persisted=False)
           ↓
    Phase 5 ready (NO Neo4j execution in Phase 4!)
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Tuple

from ..core.logging import get_logger
from ..storage.repository import get_repository
from ..utils.helpers import utcnow_iso

from . import entity_extractor, fact_extractor, relation_extractor
from .model_interface import DocLinkLLM, get_doclink_llm
from .normalizer import (
    canonicalize_references,
    deduplicate_entities,
    deduplicate_facts,
    deduplicate_relations,
    evidence_coverage,
    merge_evidence,
    resolve_coreferences,
)
from .schemas import (
    ChunkExtraction,
    DocLinkAnalyzeResponse,
    DocLinkEntity,
    DocLinkFact,
    DocLinkRelation,
    DocLinkResult,
    DocLinkStatistics,
    DocLinkValidationReport,
    ExtractionChunk,
    GraphEdge,
    GraphNode,
    GraphReadyGraph,
    RawEntity,
    RawFact,
    RawRelation,
    SourceSpan,
    UCKRProjection,
)
from .validator import validate_doclink_result

log = get_logger("doclink.service")


def chunk_document_text(
    text: str,
    document_id: str = "doc_001",
    chunk_size: int = 1800,
    page_texts: Optional[Dict[int, str]] = None,
) -> List[ExtractionChunk]:
    """Slice document text into logical chunks with page / line pointers."""
    chunks: List[ExtractionChunk] = []

    if page_texts:
        for page_num in sorted(page_texts.keys()):
            p_text = (page_texts[page_num] or "").strip()
            if not p_text:
                continue
            if len(p_text) <= chunk_size:
                cid = f"chunk_{len(chunks)+1:03d}"
                chunks.append(
                    ExtractionChunk(
                        chunk_id=cid,
                        document_id=document_id,
                        page=page_num,
                        text=p_text,
                        char_start=0,
                        char_end=len(p_text),
                        word_count=len(p_text.split()),
                    )
                )
            else:
                # Sub-slice long page
                cursor = 0
                sub_idx = 1
                while cursor < len(p_text):
                    end = min(cursor + chunk_size, len(p_text))
                    # Try breaking at newline or sentence boundary if possible
                    if end < len(p_text):
                        nl = p_text.rfind("\n", cursor, end)
                        if nl > cursor + chunk_size // 2:
                            end = nl + 1
                    slice_text = p_text[cursor:end].strip()
                    if slice_text:
                        cid = f"chunk_{len(chunks)+1:03d}"
                        chunks.append(
                            ExtractionChunk(
                                chunk_id=cid,
                                document_id=document_id,
                                page=page_num,
                                section=f"Page {page_num} part {sub_idx}",
                                text=slice_text,
                                char_start=cursor,
                                char_end=end,
                                word_count=len(slice_text.split()),
                            )
                        )
                        sub_idx += 1
                    cursor = end
        if chunks:
            return chunks

    # Default single text slicing if no page_texts provided
    clean_text = (text or "").strip()
    if not clean_text:
        return [
            ExtractionChunk(
                chunk_id="chunk_001",
                document_id=document_id,
                page=1,
                text="",
                char_start=0,
                char_end=0,
                word_count=0,
            )
        ]

    cursor = 0
    idx = 1
    while cursor < len(clean_text):
        end = min(cursor + chunk_size, len(clean_text))
        if end < len(clean_text):
            nl = clean_text.rfind("\n", cursor, end)
            if nl > cursor + chunk_size // 2:
                end = nl + 1
        sub_text = clean_text[cursor:end].strip()
        if sub_text:
            chunks.append(
                ExtractionChunk(
                    chunk_id=f"chunk_{idx:03d}",
                    document_id=document_id,
                    page=1,
                    text=sub_text,
                    char_start=cursor,
                    char_end=end,
                    word_count=len(sub_text.split()),
                )
            )
            idx += 1
        cursor = end

    return chunks if chunks else [
        ExtractionChunk(
            chunk_id="chunk_001",
            document_id=document_id,
            page=1,
            text=clean_text,
            char_start=0,
            char_end=len(clean_text),
            word_count=len(clean_text.split()),
        )
    ]


class DocLinkService:
    """Orchestrates complete DocLink Entity / Fact / Relation Engine pipeline."""

    def __init__(self, llm: Optional[DocLinkLLM] = None) -> None:
        self.llm = llm

    def _get_llm(self, use_llm: bool = True) -> DocLinkLLM:
        if self.llm is not None:
            return self.llm
        return get_doclink_llm(use_llm=use_llm)

    def analyze_text(
        self,
        text: str,
        document_id: str = "doc_001",
        document_name: str = "document",
        project_id: str = "",
        source_id: str = "",
        use_llm: bool = True,
        chunk_size: int = 1800,
        page_texts: Optional[Dict[int, str]] = None,
    ) -> DocLinkResult:
        """Run complete DocLink pipeline on raw document text."""
        log.info("Starting DocLink analysis for document '%s' (%d chars)", document_id, len(text))
        llm_instance = self._get_llm(use_llm=use_llm)

        # Step 1: Chunk document
        chunks = chunk_document_text(text, document_id=document_id, chunk_size=chunk_size, page_texts=page_texts)

        per_chunk_extractions: List[ChunkExtraction] = []
        all_raw_entities: List[Tuple[RawEntity, SourceSpan]] = []
        all_raw_facts: List[Tuple[RawFact, SourceSpan]] = []
        all_raw_relations: List[Tuple[RawRelation, SourceSpan]] = []
        global_rejected: List[str] = []
        primary_provider = getattr(llm_instance, "name", "deterministic")

        # Step 2: Per-chunk extraction
        for chunk in chunks:
            # 2a. Entity extraction
            raw_ents, rej_e, prov_e = entity_extractor.extract_entities(
                chunk.text,
                llm=llm_instance,
                chunk_id=chunk.chunk_id,
                page=chunk.page,
                section=chunk.section,
                use_llm=use_llm,
            )
            global_rejected.extend(rej_e)
            if prov_e != "deterministic":
                primary_provider = prov_e

            # 2b. Fact extraction
            raw_facts, rej_f, prov_f = fact_extractor.extract_facts(
                chunk.text,
                known_entities=[e.text for e in raw_ents],
                llm=llm_instance,
                chunk_id=chunk.chunk_id,
                page=chunk.page,
                section=chunk.section,
                use_llm=use_llm,
            )
            global_rejected.extend(rej_f)

            # 2c. Relation extraction
            raw_rels, rej_r, prov_r = relation_extractor.extract_relations(
                chunk.text,
                known_entities=raw_ents,
                llm=llm_instance,
                chunk_id=chunk.chunk_id,
                page=chunk.page,
                section=chunk.section,
                use_llm=use_llm,
            )
            global_rejected.extend(rej_r)

            # Store per-chunk extraction record
            per_chunk_extractions.append(
                ChunkExtraction(
                    chunk_id=chunk.chunk_id,
                    page=chunk.page,
                    provider=prov_e,
                    entities=raw_ents,
                    facts=raw_facts,
                    relations=raw_rels,
                    rejected=rej_e + rej_f + rej_r,
                )
            )

            # Attach evidence spans
            for e in raw_ents:
                span = SourceSpan(
                    document_id=document_id,
                    source_id=source_id or document_id,
                    chunk_id=chunk.chunk_id,
                    page=chunk.page,
                    text_span=e.quote or chunk.text[:200],
                )
                all_raw_entities.append((e, span))

            for f in raw_facts:
                span = SourceSpan(
                    document_id=document_id,
                    source_id=source_id or document_id,
                    chunk_id=chunk.chunk_id,
                    page=chunk.page,
                    text_span=f.quote or f.statement or chunk.text[:200],
                )
                all_raw_facts.append((f, span))

            for r in raw_rels:
                span = SourceSpan(
                    document_id=document_id,
                    source_id=source_id or document_id,
                    chunk_id=chunk.chunk_id,
                    page=chunk.page,
                    text_span=r.quote or chunk.text[:200],
                )
                all_raw_relations.append((r, span))

        # Step 3: Global Normalization & Deduplication
        initial_entities: List[DocLinkEntity] = []
        for idx, (raw_e, span) in enumerate(all_raw_entities, start=1):
            initial_entities.append(
                DocLinkEntity(
                    entity_id=f"ent_{idx:03d}",
                    text=raw_e.text,
                    canonical_name=raw_e.canonical_name or raw_e.text,
                    surface_forms=[raw_e.text],
                    type=raw_e.type,
                    confidence=raw_e.confidence if raw_e.confidence is not None else 0.9,
                    evidence=[span] if span.text_span else [],
                    aliases_resolved=raw_e.aliases,
                )
            )

        dedup_entities, merge_summary = deduplicate_entities(initial_entities)

        # Re-assign sequential entity IDs
        for idx, ent in enumerate(dedup_entities, start=1):
            ent.entity_id = f"ent_{idx:03d}"

        # Resolve coreferences across text chunks
        for chunk in chunks:
            resolve_coreferences(dedup_entities, chunk.text)

        # Deduplicate facts
        initial_facts: List[DocLinkFact] = []
        for idx, (raw_f, span) in enumerate(all_raw_facts, start=1):
            initial_facts.append(
                DocLinkFact(
                    fact_id=f"fact_{idx:03d}",
                    statement=raw_f.statement or f"{raw_f.subject} {raw_f.predicate} {raw_f.object}",
                    subject=raw_f.subject,
                    predicate=raw_f.predicate,
                    object=raw_f.object,
                    time=raw_f.time,
                    fact_type=raw_f.fact_type or "STATEMENT",
                    confidence=raw_f.confidence if raw_f.confidence is not None else 0.9,
                    evidence=[span] if span.text_span else [],
                )
            )
        dedup_facts, removed_facts_count = deduplicate_facts(initial_facts)
        for idx, fact in enumerate(dedup_facts, start=1):
            fact.fact_id = f"fact_{idx:03d}"

        # Deduplicate relations
        initial_relations: List[DocLinkRelation] = []
        for idx, (raw_r, span) in enumerate(all_raw_relations, start=1):
            initial_relations.append(
                DocLinkRelation(
                    relation_id=f"rel_{idx:03d}",
                    source=raw_r.source,
                    relation=raw_r.relation,
                    target=raw_r.target,
                    confidence=raw_r.confidence if raw_r.confidence is not None else 0.9,
                    evidence=[span] if span.text_span else [],
                )
            )
        dedup_relations, removed_rels_count = deduplicate_relations(initial_relations)
        for idx, rel in enumerate(dedup_relations, start=1):
            rel.relation_id = f"rel_{idx:03d}"

        # Canonicalize references in facts and relations to point to entity_ids & canonical names
        ref_stats = canonicalize_references(dedup_facts, dedup_relations, dedup_entities)

        # Step 4: Statistics
        cov_score = evidence_coverage(dedup_entities, dedup_facts, dedup_relations)
        entity_types_count: Dict[str, int] = {}
        for e in dedup_entities:
            entity_types_count[e.type] = entity_types_count.get(e.type, 0) + 1

        rel_types_count: Dict[str, int] = {}
        for r in dedup_relations:
            rel_types_count[r.relation] = rel_types_count.get(r.relation, 0) + 1

        total_ev = sum(len(e.evidence) for e in dedup_entities) + sum(len(f.evidence) for f in dedup_facts) + sum(len(r.evidence) for r in dedup_relations)

        statistics = DocLinkStatistics(
            totalChunks=len(chunks),
            totalEntities=len(dedup_entities),
            totalFacts=len(dedup_facts),
            totalRelations=len(dedup_relations),
            totalEvidence=total_ev,
            mergedEntities=merge_summary.get("mergedCount", 0),
            duplicateEntitiesRemoved=merge_summary.get("duplicatesRemoved", 0),
            duplicateFactsRemoved=removed_facts_count,
            duplicateRelationsRemoved=removed_rels_count,
            rejectedItems=len(global_rejected),
            evidenceCoverage=cov_score,
            entityTypes=entity_types_count,
            relationTypes=rel_types_count,
        )

        # Step 5: Build Graph-Ready Structure (Phase 4 -> Phase 5 hand-off contract, NOT persisted to Neo4j!)
        graph_nodes: List[GraphNode] = []
        for ent in dedup_entities:
            graph_nodes.append(
                GraphNode(
                    id=ent.entity_id,
                    label=ent.type,
                    name=ent.canonical_name,
                    type=ent.type,
                    confidence=ent.confidence,
                    properties={
                        "surface_forms": ent.surface_forms,
                        "mentions": ent.mentions,
                        "aliases_resolved": ent.aliases_resolved,
                    },
                )
            )

        graph_edges: List[GraphEdge] = []
        for rel in dedup_relations:
            src_node_id = rel.source_id or rel.source
            tgt_node_id = rel.target_id or rel.target
            graph_edges.append(
                GraphEdge(
                    id=rel.relation_id,
                    source=src_node_id,
                    type=rel.relation,
                    target=tgt_node_id,
                    confidence=rel.confidence,
                    properties={"source_name": rel.source, "target_name": rel.target},
                    evidence=rel.evidence,
                )
            )

        graph_ready = GraphReadyGraph(
            document_id=document_id,
            nodes=graph_nodes,
            edges=graph_edges,
            statistics={"node_count": len(graph_nodes), "edge_count": len(graph_edges)},
            persisted=False,  # Deliberately False (Neo4j comes in Phase 5)
        )

        # Step 6: Build UCKR Projection
        uckr_entities = [
            {
                "id": e.entity_id,
                "canonicalName": e.canonical_name,
                "type": e.type,
                "confidence": e.confidence,
                "aliases": e.surface_forms,
                "mentions": e.mentions,
            }
            for e in dedup_entities
        ]

        uckr_facts = [
            {
                "id": f.fact_id,
                "statement": f.statement,
                "subject": f.subject,
                "predicate": f.predicate,
                "object": f.object,
                "time": f.time,
                "factType": f.fact_type,
                "confidence": f.confidence,
                "sourceRefs": [sp.model_dump() for sp in f.evidence],
            }
            for f in dedup_facts
        ]

        uckr_relations = [
            {
                "id": r.relation_id,
                "source": r.source,
                "sourceId": r.source_id,
                "relation": r.relation,
                "target": r.target,
                "targetId": r.target_id,
                "confidence": r.confidence,
            }
            for r in dedup_relations
        ]

        uckr_projection = UCKRProjection(
            document_id=document_id,
            documentId=document_id,
            sourceId=source_id or document_id,
            projectId=project_id,
            phase="phase_4_doclink",
            provider=primary_provider,
            entities=uckr_entities,
            facts=uckr_facts,
            relations=uckr_relations,
            statistics=statistics,
        )

        result = DocLinkResult(
            document_id=document_id,
            documentId=document_id,
            sourceId=source_id or document_id,
            projectId=project_id,
            document_name=document_name,
            version=1,
            status="completed",
            provider=primary_provider,
            chunked=len(chunks) > 1,
            chunks=chunks,
            entities=dedup_entities,
            facts=dedup_facts,
            relations=dedup_relations,
            statistics=statistics,
            graph=graph_ready,
            uckr=uckr_projection,
        )

        # Step 7: Validation audit
        val_report = validate_doclink_result(result)
        result.validation = val_report

        log.info(
            "DocLink analysis complete for '%s': %d entities, %d facts, %d relations, %d graph nodes, %d graph edges (validation: %s)",
            document_id,
            len(dedup_entities),
            len(dedup_facts),
            len(dedup_relations),
            len(graph_nodes),
            len(graph_edges),
            val_report.status,
        )

        return result

    def analyze_document(
        self,
        document_id: str,
        project_id: str = "",
        user_id: str = "",
        use_llm: bool = True,
        chunk_size: int = 1800,
    ) -> DocLinkResult:
        """Fetch extracted document by ID and run complete DocLink pipeline."""
        sources_repo = get_repository("sources")
        doc = sources_repo.find_one({"id": document_id})
        if not doc and project_id:
            doc = sources_repo.find_one({"id": document_id, "projectId": project_id})

        text = ""
        doc_name = document_id
        page_texts: Dict[int, str] = {}

        if doc:
            doc_name = doc.get("name", document_id)
            text = doc.get("extractedText", "")
            norm = doc.get("normalized", {}) if isinstance(doc, dict) else {}
            pages = norm.get("pages", []) or []
            if pages:
                for idx, p in enumerate(pages, start=1):
                    p_text = p.get("text", "")
                    if p_text:
                        page_texts[idx] = p_text

        if not text and not page_texts:
            # Try analysis repository as fallback
            analysis_repo = get_repository("analysis")
            ana = analysis_repo.find_one({"sourceId": document_id})
            if ana:
                text = ana.get("extractedText") or ana.get("summary", "")

        if not text and not page_texts:
            log.warning("No text found for document_id '%s'; running with empty text", document_id)

        return self.analyze_text(
            text=text,
            document_id=document_id,
            document_name=doc_name,
            project_id=project_id,
            source_id=document_id,
            use_llm=use_llm,
            chunk_size=chunk_size,
            page_texts=page_texts if page_texts else None,
        )

    def link_entities(self, facts: List[Dict[str, Any]], entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Backward-compatible helper boundary method."""
        log.debug("DocLinkService.link_entities called")
        return {
            "status": "ready",
            "phase": "phase_4_doclink",
            "linkedEntities": len(entities),
            "linkedFacts": len(facts),
        }


__all__ = ["DocLinkService", "chunk_document_text"]
