"""Phase 5 Hybrid Vector + Graph RAG API Routes.

Provides:
- POST /api/rag/query   — Full RAG with answer generation
- POST /api/rag/retrieve — Pure retrieval (vector + graph + RRF fusion) without generation
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ...core.config import get_settings
from ...rag.schemas import RAGQueryRequest, RAGQueryResponse, FusionStrategyEnum
from ...rag.service import get_rag_service
from ...rag.vector_retriever import VectorRetriever
from ...rag.graph_retriever import GraphRetriever
from ...rag.query_analyzer import QueryAnalyzer
from ...rag.fusion import ResultFusion, ReciprocalRankFusion

log = logging.getLogger("gen-transform.api.routes.rag")

router = APIRouter(prefix="/api/rag", tags=["RAG Pipeline"])


# ──────────────────────────────────────────────────
# Schemas for /retrieve endpoint
# ──────────────────────────────────────────────────

class HybridRetrieveRequest(BaseModel):
    """Request for pure retrieval (no LLM generation)."""
    query: str = Field(..., min_length=1, description="Natural language search query")
    top_k: int = Field(5, ge=1, le=50, description="Final top-K results after fusion")
    document_id: Optional[str] = Field(None, description="Filter by document_id")
    fusion_strategy: str = Field("rrf", description="Fusion strategy: 'rrf' or 'weighted'")


class HybridRetrieveResultItem(BaseModel):
    """A single hybrid retrieval result with RRF provenance."""
    rank: int
    score: float
    rrf_score: float
    text: str
    document_id: str = ""
    chunk_id: str = ""
    page_number: int = 1
    retrieval_method: str = "hybrid"
    source: str = ""
    vector_rank: Optional[int] = None
    graph_rank: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HybridRetrieveResponse(BaseModel):
    """Response from /api/rag/retrieve."""
    query: str
    results: List[HybridRetrieveResultItem]
    metrics: Dict[str, Any] = Field(default_factory=dict)


# ──────────────────────────────────────────────────
# POST /api/rag/query — Full RAG (existing)
# ──────────────────────────────────────────────────

@router.post(
    "/query",
    response_model=RAGQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Hybrid Vector + Graph RAG Query",
    description=(
        "Combines semantic vector search (Phase 6) and Neo4j knowledge graph relationships (Phase 5) "
        "using result fusion and candidate reranking to generate grounded answers with source citations."
    ),
)
async def query_rag(req: RAGQueryRequest) -> RAGQueryResponse:
    """Execute Hybrid Vector + Graph RAG query."""
    if not req.query or not req.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty.",
        )

    try:
        service = get_rag_service()
        response = service.query(req)
        return response
    except Exception as exc:
        log.exception("Error executing Phase 7 RAG query for '%s': %s", req.query, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hybrid RAG execution failed: {str(exc)}",
        )


# ──────────────────────────────────────────────────
# POST /api/rag/retrieve — Pure Retrieval (Phase 5)
# ──────────────────────────────────────────────────

@router.post(
    "/retrieve",
    response_model=HybridRetrieveResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Hybrid Vector + Graph Retrieval Only",
    description=(
        "Performs REAL vector search (FAISS) + REAL graph search (Neo4j) + "
        "RRF fusion + deduplication. Returns ranked evidence without LLM generation."
    ),
)
async def retrieve_hybrid(req: HybridRetrieveRequest) -> HybridRetrieveResponse:
    """Execute hybrid retrieval: vector + graph + RRF fusion."""
    if not req.query or not req.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty.",
        )

    try:
        settings = get_settings()
        t_start = time.time()

        # Step 1: Query analysis
        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze(req.query)

        # Step 2: Vector retrieval (FAISS)
        t_vec = time.time()
        vec_retriever = VectorRetriever()
        vector_results, vector_ms = vec_retriever.retrieve(
            query=analysis.semantic_query,
            top_k=settings.vector_top_k,
            document_id=req.document_id,
        )
        actual_vector_ms = round((time.time() - t_vec) * 1000, 2)

        # Step 3: Graph retrieval (Neo4j)
        t_graph = time.time()
        graph_retriever = GraphRetriever()
        graph_results, graph_ms = graph_retriever.retrieve(
            analysis=analysis,
            graph_depth=1,
            document_id=req.document_id,
            top_k=settings.graph_top_k,
        )
        actual_graph_ms = round((time.time() - t_graph) * 1000, 2)

        # Step 4: RRF Fusion + Deduplication
        t_fusion = time.time()
        rrf_k = settings.rrf_k
        fusion_engine = ResultFusion()
        fusion_engine.rrf_fusion = ReciprocalRankFusion(k=rrf_k)

        strategy = FusionStrategyEnum.RRF if req.fusion_strategy == "rrf" else FusionStrategyEnum.WEIGHTED
        fused, agreement, conflicts, fusion_ms = fusion_engine.fuse_and_deduplicate(
            vector_results=vector_results,
            graph_results=graph_results,
            strategy=strategy,
        )
        actual_fusion_ms = round((time.time() - t_fusion) * 1000, 2)

        # Build vector/graph rank maps for provenance
        vec_rank_map = {r.source_id: idx + 1 for idx, r in enumerate(vector_results)}
        graph_rank_map = {r.source_id: idx + 1 for idx, r in enumerate(graph_results)}

        # Step 5: Build response items with provenance
        final_results = fused[:req.top_k]
        result_items: List[HybridRetrieveResultItem] = []

        for rank_idx, item in enumerate(final_results, start=1):
            page = item.metadata.get("page_start") or item.metadata.get("page") or item.evidence.get("page", 1)
            chunk_id = item.source_id
            doc_id = item.document_id or ""

            result_items.append(HybridRetrieveResultItem(
                rank=rank_idx,
                score=round(item.score, 6),
                rrf_score=round(item.score, 6),
                text=item.text,
                document_id=doc_id,
                chunk_id=chunk_id,
                page_number=int(page) if page else 1,
                retrieval_method="hybrid",
                source=item.source_type,
                vector_rank=vec_rank_map.get(chunk_id),
                graph_rank=graph_rank_map.get(chunk_id),
                metadata=item.metadata,
            ))

        total_ms = round((time.time() - t_start) * 1000, 2)

        return HybridRetrieveResponse(
            query=req.query,
            results=result_items,
            metrics={
                "vector_results": len(vector_results),
                "graph_results": len(graph_results),
                "fused_candidates": len(fused),
                "final_results": len(result_items),
                "embedding_time_ms": vector_ms,
                "faiss_search_time_ms": actual_vector_ms,
                "neo4j_search_time_ms": actual_graph_ms,
                "fusion_time_ms": actual_fusion_ms,
                "total_time_ms": total_ms,
                "rrf_k": rrf_k,
                "fusion_strategy": req.fusion_strategy,
                "agreement_detected": agreement,
                "potential_conflicts": len(conflicts),
            },
        )

    except Exception as exc:
        log.exception("Error executing hybrid retrieval for '%s': %s", req.query, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hybrid retrieval failed: {str(exc)}",
        )


# ──────────────────────────────────────────────────
# POST /api/rag/answer — Phase 7 Final Grounded RAG
# ──────────────────────────────────────────────────

class GroundedAnswerRequest(BaseModel):
    """Request for Phase 7 final grounded RAG answer generation."""
    query: str = Field(..., min_length=1, description="Target question")
    top_k: int = Field(5, ge=1, le=50, description="RRF candidate pool limit")
    qubo_k: int = Field(3, ge=1, le=50, description="QUBO selected evidence count K")
    enable_qubo: bool = Field(True, description="Enable QUBO evidence selection")
    max_new_tokens: int = Field(256, ge=16, le=1024, description="Max tokens for student answer")


class GroundedAnswerResponse(BaseModel):
    """Response payload for POST /api/rag/answer."""
    query: str
    answer: str
    citations: List[str]
    evidence: List[Dict[str, Any]]
    retrieval: Dict[str, Any]
    qubo: Dict[str, Any]
    model: Dict[str, Any]
    grounding: Dict[str, Any]
    total_latency_ms: float


@router.get(
    "/answer/status",
    status_code=status.HTTP_200_OK,
    summary="Get Phase 7 Grounded RAG Pipeline Status",
)
async def get_rag_answer_status():
    """Return operational availability of grounded RAG pipeline."""
    from ...services.student_service import get_student_service
    student_status = get_student_service().get_status()
    return {
        "status": "ready",
        "pipeline": "FAISS + Neo4j -> RRF -> QUBO -> QLoRA Student",
        "student": student_status,
    }


@router.post(
    "/answer",
    response_model=GroundedAnswerResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Phase 7 Final Grounded RAG Generation",
    description=(
        "Full Phase 7 pipeline: FAISS + Neo4j retrieval -> RRF fusion -> QUBO evidence selection -> "
        "Context builder -> QLoRA student model -> Grounding & Citation validator."
    ),
)
async def generate_grounded_answer(req: GroundedAnswerRequest) -> GroundedAnswerResponse:
    """Execute complete grounded RAG question answering."""
    if not req.query or not req.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty.",
        )

    if len(req.query) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query exceeds maximum length of 1000 characters.",
        )

    if req.qubo_k > req.top_k:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"qubo_k ({req.qubo_k}) cannot be greater than top_k ({req.top_k}).",
        )

    try:
        from ...rag.grounded_rag import get_grounded_rag_service
        service = get_grounded_rag_service()
        res = service.answer_query(
            query=req.query,
            top_k=req.top_k,
            qubo_k=req.qubo_k,
            enable_qubo=req.enable_qubo,
            max_new_tokens=req.max_new_tokens,
        )

        return GroundedAnswerResponse(
            query=res["query"],
            answer=res["answer"],
            citations=res["citations"],
            evidence=res["evidence"],
            retrieval=res["retrieval"],
            qubo=res["qubo"],
            model=res["model"],
            grounding=res["grounding"],
            total_latency_ms=res["latency_breakdown_ms"]["total_ms"],
        )

    except Exception as exc:
        log.exception("Error generating grounded RAG answer for '%s': %s", req.query, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Grounded RAG answer generation failed: {str(exc)}",
        )

