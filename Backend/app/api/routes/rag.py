"""Phase 7 Hybrid Vector + Graph RAG API Routes.

Provides POST /api/rag/query for executing natural language Hybrid Vector + Graph RAG searches.
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, status

from ...rag.schemas import RAGQueryRequest, RAGQueryResponse
from ...rag.service import get_rag_service

log = logging.getLogger("gen-transform.api.routes.rag")

router = APIRouter(prefix="/api/rag", tags=["RAG Pipeline"])


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
