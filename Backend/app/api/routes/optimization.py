"""Phase 8 Quantum / Hybrid Optimization API Routes.

Provides POST /api/optimization/select for executing standalone evidence subset optimization.
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, status

from ...optimization.schemas import OptimizationSelectRequest, OptimizationSelectResponse
from ...optimization.service import get_optimization_service
from ...rag.schemas import RetrievalResult

log = logging.getLogger("gen-transform.api.routes.optimization")

router = APIRouter(prefix="/api/optimization", tags=["Quantum/Hybrid Optimization Layer"])


@router.post(
    "/select",
    response_model=OptimizationSelectResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Evidence Subset Selection Optimization",
    description=(
        "Optimizes retrieval candidate selection using Classical, Quantum (QUBO), or Hybrid solvers. "
        "Maximizes relevance, graph coverage, source diversity, and evidence quality while enforcing context token budgets."
    ),
)
async def select_optimal_candidates(req: OptimizationSelectRequest) -> OptimizationSelectResponse:
    """Execute standalone candidate evidence optimization."""
    if not req.query or not req.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty.",
        )

    if not req.candidates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Candidate list cannot be empty.",
        )

    try:
        # Map input candidate dicts to RetrievalResult models
        retrieval_candidates = []
        for c in req.candidates:
            retrieval_candidates.append(
                RetrievalResult(
                    source_type=c.get("source_type", "vector"),
                    source_id=str(c.get("source_id") or c.get("id") or "cand_001"),
                    document_id=str(c.get("document_id") or c.get("doc_id") or "doc_001"),
                    text=str(c.get("text") or ""),
                    score=float(c.get("score") or c.get("relevance") or 0.8),
                    metadata=c.get("metadata") or {},
                    evidence=c.get("evidence") or {},
                )
            )

        service = get_optimization_service()
        selected_retrieval, meta = service.optimize_candidates(
            query=req.query,
            candidates=retrieval_candidates,
            backend=req.backend,
            max_selected=req.max_selected,
            max_tokens=req.max_tokens,
        )

        selected_dicts = [c.model_dump() for c in selected_retrieval]

        return OptimizationSelectResponse(
            query=req.query,
            selected_candidates=selected_dicts,
            optimization=meta,
        )

    except Exception as exc:
        log.exception("Error executing optimization selection for '%s': %s", req.query, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Candidate selection optimization failed: {str(exc)}",
        )
