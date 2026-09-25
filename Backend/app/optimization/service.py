"""Phase 8 Quantum / Hybrid Optimization — Service Orchestrator.

Orchestrates candidate selection optimization for Phase 7 RAG candidates,
selecting optimal evidence subsets using classical, quantum, or hybrid solvers
with zero modification to source facts and automatic fail-safe fallback.
"""
from __future__ import annotations

import time
import logging
from typing import Dict, List, Optional, Tuple

from ..rag.schemas import RetrievalResult
from .classical_solver import ClassicalOptimizer
from .config import OptimizationConfig, default_optimization_config
from .hybrid_solver import HybridOptimizer
from .problem import ProblemFormulator
from .quantum_solver import QuantumOptimizer
from .schemas import OptimizationMetadata, OptimizationResultSchema

log = logging.getLogger("gen-transform.optimization.service")


class OptimizationService:
    """Complete Phase 8 Optimization Pipeline Service."""

    def __init__(self, config: Optional[OptimizationConfig] = None) -> None:
        self.config = config or default_optimization_config
        self.formulator = ProblemFormulator(self.config)
        self.classical_solver = ClassicalOptimizer(self.config)
        self.quantum_solver = QuantumOptimizer(self.config)
        self.hybrid_solver = HybridOptimizer(self.config)

    def optimize_candidates(
        self,
        query: str,
        candidates: List[RetrievalResult],
        backend: Optional[str] = None,
        max_selected: Optional[int] = None,
        max_tokens: Optional[int] = None,
    ) -> Tuple[List[RetrievalResult], OptimizationMetadata]:
        """Select optimal candidate subset using classical, quantum, or hybrid optimization."""
        t_start = time.time()
        clean_query = (query or "").strip()
        n_before = len(candidates)

        effective_backend = (backend or self.config.backend or "hybrid").lower()
        effective_max_selected = max_selected or self.config.max_selected_candidates
        effective_max_tokens = max_tokens or self.config.max_context_tokens

        # Check if optimization layer is active
        if not self.config.enabled or not candidates:
            latency_ms = round((time.time() - t_start) * 1000, 2)
            meta = OptimizationMetadata(
                enabled=self.config.enabled,
                backend=effective_backend,
                candidates_before=n_before,
                candidates_after=n_before,
                objective_value=1.0,
                constraints_satisfied=True,
                latency_ms=latency_ms,
                solver_used="bypass",
                fallback_triggered=False,
            )
            return candidates[:effective_max_selected], meta

        # Step 1: Formulate optimization problem
        problem = self.formulator.build_problem(
            query=clean_query,
            candidates=candidates,
            max_selected=effective_max_selected,
            max_tokens=effective_max_tokens,
        )

        # Step 2: Execute chosen solver with automatic fail-safe fallback
        fallback_triggered = False
        res: Optional[OptimizationResultSchema] = None

        if effective_backend == "classical":
            res = self.classical_solver.optimize(problem)

        elif effective_backend == "quantum":
            try:
                res = self.quantum_solver.optimize(problem)
            except Exception as exc:
                log.warning("Quantum optimization backend failed (%s); executing classical fallback", exc)
                res = self.classical_solver.optimize(problem)
                res.solver_used = "classical_fallback"
                fallback_triggered = True

        else:  # 'hybrid' or default
            try:
                res = self.hybrid_solver.optimize(problem)
            except Exception as exc:
                log.warning("Hybrid optimization backend failed (%s); executing classical fallback", exc)
                res = self.classical_solver.optimize(problem)
                res.solver_used = "classical_fallback"
                fallback_triggered = True

        # Step 3: Extract optimized subset maintaining exact candidate integrity
        selected_set = set(res.selected_candidate_ids) if res else set()
        optimized_candidates = [c for c in candidates if c.source_id in selected_set]

        # Safety: If solver returned empty set unexpectedly, fallback to top candidates
        if not optimized_candidates and candidates:
            log.warning("Optimization solver returned empty selection; keeping top candidates.")
            optimized_candidates = candidates[:effective_max_selected]
            fallback_triggered = True

        latency_ms = round((time.time() - t_start) * 1000, 2)

        metadata = OptimizationMetadata(
            enabled=True,
            backend=effective_backend,
            candidates_before=n_before,
            candidates_after=len(optimized_candidates),
            objective_value=res.objective_value if res else 0.0,
            constraints_satisfied=res.constraints_satisfied if res else True,
            latency_ms=latency_ms,
            solver_used=res.solver_used if res else "unknown",
            fallback_triggered=fallback_triggered or getattr(res, "fallback_triggered", False),
        )

        log.info(
            "Phase 8 optimization (%s): %d -> %d candidates, obj=%.4f in %sms",
            metadata.solver_used,
            n_before,
            len(optimized_candidates),
            metadata.objective_value,
            latency_ms,
        )

        return optimized_candidates, metadata


_OPTIMIZATION_SERVICE_INSTANCE: Optional[OptimizationService] = None


def get_optimization_service() -> OptimizationService:
    """Return singleton instance of OptimizationService."""
    global _OPTIMIZATION_SERVICE_INSTANCE
    if _OPTIMIZATION_SERVICE_INSTANCE is None:
        _OPTIMIZATION_SERVICE_INSTANCE = OptimizationService()
    return _OPTIMIZATION_SERVICE_INSTANCE


def reset_optimization_service() -> None:
    """Reset singleton instance for testing."""
    global _OPTIMIZATION_SERVICE_INSTANCE
    _OPTIMIZATION_SERVICE_INSTANCE = None


__all__ = ["OptimizationService", "get_optimization_service", "reset_optimization_service"]
