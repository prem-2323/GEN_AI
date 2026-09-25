"""Embeddings & Vector Search (Phase 6) API Routes.

Endpoints:
- POST /api/embeddings/index/{document_id}
- POST /api/embeddings/index-text
- POST /api/embeddings/search
- DELETE /api/embeddings/document/{document_id}
- GET /api/embeddings/document/{document_id}
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependencies import get_workspace_identity
from ...embeddings.models import IndexDocumentResponse, SearchRequest
from ...embeddings.service import EmbeddingPipelineService

router = APIRouter(prefix="/api/embeddings", tags=["embeddings"])
embeddings_service = EmbeddingPipelineService()


@router.post("/index-text", response_model=IndexDocumentResponse, status_code=200)
async def index_text_endpoint(
    payload: Dict[str, Any],
    user: dict = Depends(get_workspace_identity),
):
    """Index arbitrary text using Phase 6 semantic chunking and embedding pipeline."""
    text = payload.get("text", "")
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Text field cannot be empty.")

    doc_id = payload.get("document_id") or payload.get("documentId") or "doc_inline"
    filename = payload.get("source_filename") or payload.get("name") or "inline.txt"

    return embeddings_service.index_text(
        text=text,
        document_id=doc_id,
        source_filename=filename,
    )


@router.post("/index/{document_id}", response_model=IndexDocumentResponse, status_code=200)
async def index_document_endpoint(
    document_id: str,
    user: dict = Depends(get_workspace_identity),
):
    """Fetch stored document and run Phase 6 semantic chunking & vector indexing."""
    try:
        return embeddings_service.index_document(document_id=document_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Document indexing failed: {exc}")


@router.post("/search", status_code=200)
async def semantic_search_endpoint(
    req: SearchRequest,
    user: dict = Depends(get_workspace_identity),
):
    """Perform top-K semantic similarity search over indexed vector store."""
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")

    results, latency_ms = embeddings_service.search(
        query=req.query,
        top_k=req.top_k,
        document_id=req.document_id,
        section=req.section,
        min_score=req.min_score,
    )

    return {
        "ok": True,
        "query": req.query,
        "top_k": req.top_k,
        "results_count": len(results),
        "search_latency_ms": latency_ms,
        "results": [r.model_dump() for r in results],
    }


@router.delete("/document/{document_id}")
async def delete_document_vectors_endpoint(
    document_id: str,
    user: dict = Depends(get_workspace_identity),
):
    """Delete all vectors and metadata associated with document_id."""
    deleted_count = embeddings_service.delete_document_vectors(document_id)
    return {
        "ok": True,
        "document_id": document_id,
        "deleted_count": deleted_count,
    }


@router.get("/status", status_code=200)
async def get_embeddings_status_endpoint(
    user: dict = Depends(get_workspace_identity),
):
    """Get active embedding provider status, model name, dimension, and device info."""
    return embeddings_service.get_embedding_status()


@router.get("/document/{document_id}")
async def get_document_vectors_status_endpoint(
    document_id: str,
    user: dict = Depends(get_workspace_identity),
):
    """Get vector indexing status and chunk metadata for a document_id."""
    return embeddings_service.get_document_status(document_id)


__all__ = ["router"]
