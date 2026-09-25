"""Phase 8 Quantum / Hybrid Optimization — Hybrid Solver Engine.

Executes 4-Step Hybrid Optimization Flow:
1. Classical Preprocessing (candidate reduction & filtering)
2. QUBO Formulation
3. Quantum / Mock Quantum Optimization
4. Classical Postprocessing & Hard Constraint Validation.
"""
from __future__ import annotations

import time
import logging
from typing import List

from .classical_solver import ClassicalOptimizer
from .config import OptimizationConfig, default_optimization_config
from .constraints import ConstraintManager
from .objective import ObjectiveCalculator
from .problem import ProblemFormulator
from .quantum_solver import MockQuantumOptimizer, QuantumOptimizer
from .schemas import OptimizationProblemSchema, OptimizationResultSchema

log = logging.getLogger("gen-transform.optimization.hybrid_solver")


class HybridOptimizer:
    """Combines classical candidate reduction with quantum QUBO optimization & classical postprocessing."""

    def __init__(self, config: OptimizationConfig = default_optimization_config) -> None:
        self.config = config
        self.classical_solver = ClassicalOptimizer(config)
        self.quantum_solver = QuantumOptimizer(config)
        self.problem_formulator = ProblemFormulator(config)
        self.constraint_mgr = ConstraintManager(config)
        self.objective_calc = ObjectiveCalculator(config)

    def optimize(self, problem: OptimizationProblemSchema) -> OptimizationResultSchema:
        t_start = time.time()
        candidates = problem.candidates
        n_before = len(candidates)

        if n_before == 0:
            return OptimizationResultSchema(
                selected_candidate_ids=[],
                objective_value=0.0,
                solver_used="hybrid",
                latency_ms=0.0,
                constraints_satisfied=True,
                candidates_before=0,
                candidates_after=0,
            )

        # Step 1: Classical Preprocessing (Candidate Reduction if > 30 items)
        if n_before > 30:
            log.debug("Hybrid solver filtering %d candidates down to top 30 for QUBO formulation", n_before)
            candidates.sort(
                key=lambda c: (c.relevance_score * 0.5 + c.graph_score * 0.3 + c.evidence_quality * 0.2),
                reverse=True,
            )
            reduced_candidates = candidates[:30]
            reduced_problem = self.problem_formulator.build_problem(
                query=problem.query,
                candidates=[
                    c for c in problem.candidates
                    if c.candidate_id in {rc.candidate_id for rc in reduced_candidates}
                ],
                max_selected=problem.max_selected_candidates,
                max_tokens=problem.max_context_tokens,
            )
        else:
            reduced_problem = problem

        # Step 2 & 3: Quantum / QUBO Solver Execution
        fallback_used = False
        try:
            quantum_res = self.quantum_solver.optimize(reduced_problem)
            selected_ids = quantum_res.selected_candidate_ids
            qubo_size = quantum_res.qubo_matrix_size
        except Exception as exc:
            log.warning("Quantum solver step failed in hybrid flow (%s); falling back to classical solver", exc)
            classical_res = self.classical_solver.optimize(reduced_problem)
            selected_ids = classical_res.selected_candidate_ids
            qubo_size = None
            fallback_used = True

        # Step 4: Classical Postprocessing & Hard Constraint Validation
        # Map selected IDs to decision bit array for validation
        final_bits = [1 if c.candidate_id in selected_ids else 0 for c in reduced_problem.candidates]
        valid, violations = self.constraint_mgr.is_valid(reduced_problem, final_bits)

        if not valid:
            log.debug("Hybrid quantum selection breached hard constraints (%s); fixing with classical postprocessing", violations)
            clean_res = self.classical_solver.optimize(reduced_problem)
            selected_ids = clean_res.selected_candidate_ids
            final_bits = [1 if c.candidate_id in selected_ids else 0 for c in reduced_problem.candidates]
            valid = True

        final_obj = self.objective_calc.evaluate(reduced_problem, final_bits)
        latency_ms = round((time.time() - t_start) * 1000, 2)

        log.debug(
            "Hybrid solver complete: in=%d -> selected=%d, obj=%.4f, fallback=%s in %sms",
            n_before,
            len(selected_ids),
            final_obj,
            fallback_used,
            latency_ms,
        )

        return OptimizationResultSchema(
            selected_candidate_ids=selected_ids,
            objective_value=final_obj,
            solver_used="hybrid",
            latency_ms=latency_ms,
            constraints_satisfied=valid,
            candidates_before=n_before,
            candidates_after=len(selected_ids),
            qubo_matrix_size=qubo_size,
            fallback_triggered=fallback_used,
        )


__all__ = ["HybridOptimizer"]
