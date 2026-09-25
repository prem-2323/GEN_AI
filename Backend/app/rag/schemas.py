"""Phase 7 Hybrid Vector + Graph RAG Schemas."""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FusionStrategyEnum(str, Enum):
    WEIGHTED = "weighted"
    RRF = "rrf"


class QueryTypeEnum(str, Enum):
    SEMANTIC = "SEMANTIC"
    GRAPH = "GRAPH"
    HYBRID = "HYBRID"


class QueryAnalysis(BaseModel):
    query: str
    entities: List[str] = Field(default_factory=list)
    intent: str = "general_qa"
    keywords: List[str] = Field(default_factory=list)
    possible_graph_entities: List[str] = Field(default_factory=list)
    semantic_query: str
    query_type: QueryTypeEnum = QueryTypeEnum.HYBRID


class RetrievalResult(BaseModel):
    source_type: str = Field(..., description="'vector' or 'graph'")
    source_id: str
    document_id: Optional[str] = None
    text: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    evidence: Dict[str, Any] = Field(default_factory=dict)


class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language search query")
    top_k: int = Field(5, ge=1, le=50, description="Top-K vector results to retrieve")
    graph_depth: int = Field(1, ge=1, le=5, description="Graph traversal depth")
    document_id: Optional[str] = Field(None, description="Filter by target document_id")
    rerank: bool = Field(True, description="Enable candidate reranking")
    fusion_strategy: FusionStrategyEnum = Field(
        FusionStrategyEnum.WEIGHTED, description="Fusion algorithm: 'weighted' or 'rrf'"
    )
    vector_weight: float = Field(0.6, ge=0.0, le=1.0, description="Weight for vector search in fusion")
    graph_weight: float = Field(0.4, ge=0.0, le=1.0, description="Weight for graph search in fusion")
    min_retrieval_score: float = Field(0.0, ge=0.0, le=1.0, description="Minimum acceptable retrieval score")


class SourceCitation(BaseModel):
    citation_id: str
    document_id: str
    chunk_id: str
    page: Optional[int] = None
    title: Optional[str] = None


class GraphEvidence(BaseModel):
    source: str
    relation: str
    target: str
    document_id: Optional[str] = None
    confidence: float = 0.0
    evidence_text: Optional[str] = None


class RetrievalMetadata(BaseModel):
    vector_results: int = 0
    graph_results: int = 0
    candidate_count: int = 0
    final_context_items: int = 0
    query_analysis_ms: float = 0.0
    vector_ms: float = 0.0
    graph_ms: float = 0.0
    fusion_ms: float = 0.0
    rerank_ms: float = 0.0
    generation_ms: float = 0.0
    total_ms: float = 0.0
    agreement_detected: bool = False
    potential_conflicts: List[Dict[str, Any]] = Field(default_factory=list)


class RAGQueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[SourceCitation] = Field(default_factory=list)
    graph_evidence: List[GraphEvidence] = Field(default_factory=list)
    retrieval: RetrievalMetadata
    insufficient_evidence: bool = False
    query_analysis: Optional[QueryAnalysis] = None
    optimization: Optional[Dict[str, Any]] = None

