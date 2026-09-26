"""Phase 6 QUBO API Routes.

Provides:
- POST /api/qubo/optimize for executing candidate selection QUBO optimization.
- GET /api/qubo/status for inspecting QUBO solver and quantum backend availability.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ...optimization.config import OptimizationConfig, default_optimization_config
from ...optimization.qubo_matrix import QUBOFormulator, QUBOProblem, evaluate_objective_breakdown
from ...optimization.schemas import CandidateFeatureVector
from ...optimization.solvers import DWaveQUBOSolver, ExactQUBOSolver, get_qubo_solver

log = logging.getLogger("gen-transform.api.routes.qubo")

router = APIRouter(prefix="/api/qubo", tags=["Phase 6 QUBO Evidence Selection Layer"])


class QUBOOptimizeRequest(BaseModel):
    """Request payload for POST /api/qubo/optimize."""

    candidates: List[Dict[str, Any]] = Field(..., description="List of candidate evidence dicts or feature vectors")
    target_k: Optional[int] = Field(None, ge=1, le=50, description="Target candidate selection cardinality K")
    weights: Optional[Dict[str, float]] = Field(None, description="Optional weight overrides: relevance_weight, etc.")
    solver: Optional[str] = Field("auto", description="'auto', 'exact', 'simulated_annealing', or 'quantum'")
    seed: Optional[int] = Field(42, description="Random seed for simulated annealing reproducibility")


class QUBOOptimizeResponse(BaseModel):
    """Response payload for POST /api/qubo/optimize."""

    solver_type: str = Field(..., description="'classical_exact', 'classical_simulated_annealing', or 'quantum_dwave'")
    candidate_count: int
    target_k: int
    selected_count: int
    selected_candidate_ids: List[str]
    selected_candidates: List[Dict[str, Any]]
    binary_solution: List[int]
    total_energy: float
    objective_breakdown: Dict[str, float]
    qubo_matrix_metadata: Dict[str, Any]
    optimization_time_ms: float
    quantum_backend_available: bool = False


class QUBOStatusResponse(BaseModel):
    """Response payload for GET /api/qubo/status."""

    enabled: bool
    backend: str
    solver: str
    quantum_backend_available: bool


@router.get(
    "/status",
    response_model=QUBOStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get QUBO Optimization Layer Status",
)
async def get_qubo_status() -> QUBOStatusResponse:
    """Return status of QUBO layer, active solver, and quantum hardware backend status."""
    cfg = default_optimization_config
    dwave_check = DWaveQUBOSolver(cfg)
    return QUBOStatusResponse(
        enabled=cfg.enabled,
        backend=cfg.backend,
        solver=cfg.solver,
        quantum_backend_available=dwave_check.is_quantum_available(),
    )


@router.post(
    "/optimize",
    response_model=QUBOOptimizeResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Mathematical QUBO Candidate Evidence Selection",
)
async def optimize_qubo(req: QUBOOptimizeRequest) -> QUBOOptimizeResponse:
    """Formulate matrix Q and solve min_x x^T Q x over binary variables x_i in {0,1}."""
    if not req.candidates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Candidate list cannot be empty.",
        )

    try:
        # Convert candidate dicts into CandidateFeatureVector objects
        feature_vectors = []
        for idx, c in enumerate(req.candidates):
            cand_id = str(c.get("candidate_id") or c.get("chunk_id") or c.get("id") or f"cand_{idx:03d}")
            text = str(c.get("text") or c.get("content") or "")
            doc_id = str(c.get("document_id") or c.get("doc_id") or "doc_default")
            rel_score = float(c.get("relevance_score") or c.get("similarity") or c.get("score") or 0.8)
            g_score = float(c.get("graph_score") or c.get("graph_relevance") or 0.5)
            ev_qual = float(c.get("evidence_quality") or c.get("quality") or 0.9)

            feature_vectors.append(
                CandidateFeatureVector(
                    candidate_id=cand_id,
                    source_type=str(c.get("source_type") or c.get("retrieval_method") or "vector"),
                    document_id=doc_id,
                    text=text,
                    relevance_score=rel_score,
                    graph_score=g_score,
                    evidence_quality=ev_qual,
                    metadata=c.get("metadata") or {},
                )
            )

        # Build QUBO Problem
        cfg = OptimizationConfig()
        if req.seed is not None:
            cfg.seed = req.seed

        formulator = QUBOFormulator(cfg)
        qubo_problem = formulator.build_qubo(
            candidates=feature_vectors,
            target_k=req.target_k,
            weights=req.weights,
        )

        # Solve problem
        solver = get_qubo_solver(
            solver_name=req.solver,
            candidate_count=len(feature_vectors),
            config=cfg,
        )
        res = solver.solve(qubo_problem)

        # Map selected IDs back to input candidate dicts
        selected_set = set(res.selected_candidate_ids)
        selected_cand_dicts = [c for c in req.candidates if str(c.get("candidate_id") or c.get("chunk_id") or c.get("id")) in selected_set]
        if not selected_cand_dicts:
            # Fallback mapping if IDs differed
            selected_cand_dicts = [req.candidates[i] for i, b in enumerate(res.binary_solution) if b == 1]

        return QUBOOptimizeResponse(
            solver_type=res.solver_type,
            candidate_count=len(feature_vectors),
            target_k=qubo_problem.target_k,
            selected_count=len(res.selected_candidate_ids),
            selected_candidate_ids=res.selected_candidate_ids,
            selected_candidates=selected_cand_dicts,
            binary_solution=res.binary_solution,
            total_energy=res.total_energy,
            objective_breakdown=res.objective_breakdown,
            qubo_matrix_metadata={
                "matrix_shape": [len(feature_vectors), len(feature_vectors)],
                "constant_offset": qubo_problem.constant_offset,
                "representation": qubo_problem.representation,
            },
            optimization_time_ms=res.latency_ms,
            quantum_backend_available=res.quantum_backend_available,
        )

    except Exception as exc:
        log.exception("Error during QUBO optimization: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"QUBO optimization execution failed: {str(exc)}",
        )
