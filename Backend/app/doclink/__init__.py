"""DocLink Module (Phase 4): Entity, Fact, and Relation Engine.

Converts raw extracted document text into machine-readable knowledge representations,
UCKR projections, and graph-ready structures for Phase 5 (Neo4j).
"""
from __future__ import annotations

from .entity_extractor import extract_entities, extract_entities_deterministic
from .fact_extractor import extract_facts, extract_facts_deterministic
from .model_interface import DocLinkLLM, configure_doclink_llm, get_doclink_llm
from .normalizer import (
    canonicalize_references,
    deduplicate_entities,
    deduplicate_facts,
    deduplicate_relations,
    resolve_coreferences,
)
from .relation_extractor import extract_relations, extract_relations_deterministic
from .schemas import (
    DocLinkAnalyzeRequest,
    DocLinkAnalyzeResponse,
    DocLinkEntity,
    DocLinkFact,
    DocLinkRelation,
    DocLinkResult,
    DocLinkStatistics,
    DocLinkValidationReport,
    EntityType,
    FactType,
    GraphEdge,
    GraphNode,
    GraphReadyGraph,
    RelationType,
    SourceSpan,
    UCKRProjection,
)
from .service import DocLinkService, chunk_document_text
from .validator import validate_doclink_result, validate_raw_entities, validate_raw_facts, validate_raw_relations

__all__ = [
    "DocLinkService",
    "chunk_document_text",
    "extract_entities",
    "extract_entities_deterministic",
    "extract_facts",
    "extract_facts_deterministic",
    "extract_relations",
    "extract_relations_deterministic",
    "deduplicate_entities",
    "deduplicate_facts",
    "deduplicate_relations",
    "canonicalize_references",
    "resolve_coreferences",
    "validate_doclink_result",
    "validate_raw_entities",
    "validate_raw_facts",
    "validate_raw_relations",
    "DocLinkLLM",
    "get_doclink_llm",
    "configure_doclink_llm",
    "EntityType",
    "RelationType",
    "FactType",
    "SourceSpan",
    "DocLinkEntity",
    "DocLinkFact",
    "DocLinkRelation",
    "DocLinkResult",
    "DocLinkStatistics",
    "DocLinkValidationReport",
    "GraphNode",
    "GraphEdge",
    "GraphReadyGraph",
    "UCKRProjection",
    "DocLinkAnalyzeRequest",
    "DocLinkAnalyzeResponse",
]
