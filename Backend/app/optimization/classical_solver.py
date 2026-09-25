"""Phase 8 Quantum / Hybrid Optimization — Classical Solver Baseline.

Fast, deterministic classical solver providing a reliable baseline for candidate evidence selection.
"""
from __future__ import annotations

import time
import logging
from typing import List

from .config import OptimizationConfig, default_optimization_config
from .constraints import ConstraintManager
from .objective import ObjectiveCalculator
from .schemas import OptimizationProblemSchema, OptimizationResultSchema

log = logging.getLogger("gen-transform.optimization.classical_solver")


class ClassicalOptimizer:
    """Classical optimization solver using greedy marginal gain & constraint checking."""

    def __init__(self, config: OptimizationConfig = default_optimization_config) -> None:
        self.config = config
        self.objective_calc = ObjectiveCalculator(config)
        self.constraint_mgr = ConstraintManager(config)

    def optimize(self, problem: OptimizationProblemSchema) -> OptimizationResultSchema:
        t_start = time.time()
        candidates = problem.candidates
        n = len(candidates)

        if n == 0:
            return OptimizationResultSchema(
                selected_candidate_ids=[],
                objective_value=0.0,
                solver_used="classical",
                latency_ms=0.0,
                constraints_satisfied=True,
                candidates_before=0,
                candidates_after=0,
            )

        # 1. Rank candidates by individual utility ratio (relevance + graph / sqrt(token_cost))
        ranked_indices = list(range(n))
        ranked_indices.sort(
            key=lambda i: (
                (candidates[i].relevance_score * 0.5 + candidates[i].graph_score * 0.3 + candidates[i].evidence_quality * 0.2)
                / (max(10, candidates[i].token_cost) ** 0.5)
            ),
            reverse=True,
        )

        # 2. Greedy construction with constraint check & marginal gain
        selected_bits = [0] * n
        current_tokens = 0
        current_count = 0

        best_bits = list(selected_bits)
        best_obj = 0.0

        for idx in ranked_indices:
            cand = candidates[idx]

            # Check hard boundary limits before adding
            if current_count + 1 > problem.max_selected_candidates:
                continue
            if current_tokens + cand.token_cost > problem.max_context_tokens:
                continue

            # Try adding item
            test_bits = list(selected_bits)
            test_bits[idx] = 1

            valid, _ = self.constraint_mgr.is_valid(problem, test_bits)
            if not valid:
                continue

            test_obj = self.objective_calc.evaluate(problem, test_bits)

            # Accept if objective improves or if current selection is empty
            if test_obj > best_obj or current_count == 0:
                selected_bits[idx] = 1
                current_count += 1
                current_tokens += cand.token_cost
                best_obj = test_obj
                best_bits = list(selected_bits)

        selected_ids = [candidates[i].candidate_id for i, x in enumerate(best_bits) if x == 1]
        satisfied, _ = self.constraint_mgr.is_valid(problem, best_bits)

        latency_ms = round((time.time() - t_start) * 1000, 2)
        log.debug("Classical solver completed: selected=%d/%d in %sms", len(selected_ids), n, latency_ms)

        return OptimizationResultSchema(
            selected_candidate_ids=selected_ids,
            objective_value=best_obj,
            solver_used="classical",
            latency_ms=latency_ms,
            constraints_satisfied=satisfied,
            candidates_before=n,
            candidates_after=len(selected_ids),
        )


__all__ = ["ClassicalOptimizer"]
