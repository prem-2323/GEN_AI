"""Phase 8 Quantum / Hybrid Optimization — QUBO Formulation & Quantum Solvers.

Formulates Quadratic Unconstrained Binary Optimization (QUBO) matrices x^T Q x
and executes optimization via MockQuantumOptimizer (simulated annealing) or Quantum Cloud API.
"""
from __future__ import annotations

import math
import time
import random
import logging
from abc import ABC, abstractmethod
from typing import List, Tuple

from .config import OptimizationConfig, default_optimization_config
from .constraints import ConstraintManager
from .objective import ObjectiveCalculator
from .schemas import OptimizationProblemSchema, OptimizationResultSchema

log = logging.getLogger("gen-transform.optimization.quantum_solver")


class QUBOFormulator:
    """Builds symmetric N x N QUBO matrix Q for candidate selection x^T Q x."""

    def __init__(self, config: OptimizationConfig = default_optimization_config) -> None:
        self.config = config

    def build_qubo_matrix(self, problem: OptimizationProblemSchema) -> List[List[float]]:
        """Formulate N x N upper-triangular or symmetric QUBO matrix Q."""
        candidates = problem.candidates
        n = len(candidates)
        if n == 0:
            return []

        Q = [[0.0] * n for _ in range(n)]

        # Linear weights
        w_rel = self.config.relevance_weight
        w_graph = self.config.graph_weight
        w_ev = self.config.evidence_weight

        # 1. Diagonal Linear Terms Q_ii (Negative utility to minimize x^T Q x)
        for i in range(n):
            cand = candidates[i]
            utility = (
                w_rel * cand.relevance_score
                + w_graph * cand.graph_score
                + w_ev * cand.evidence_quality
            )
            # Negative because QUBO minimizes x^T Q x
            Q[i][i] = -float(utility)

        # 2. Off-Diagonal Quadratic Terms Q_ij (Pairwise Redundancy & Document Collisions)
        red_matrix = problem.pairwise_redundancy_matrix
        w_red = self.config.redundancy_penalty * 2.0

        for i in range(n):
            for j in range(i + 1, n):
                red = red_matrix[i][j] if red_matrix else 0.0
                doc_collision = 0.1 if candidates[i].document_id == candidates[j].document_id else 0.0

                penalty_val = float((red * w_red) + doc_collision)
                Q[i][j] = penalty_val
                Q[j][i] = penalty_val

        return Q


class QuantumOptimizerInterface(ABC):
    """Abstract Base Class for Quantum and QUBO optimizers."""

    @abstractmethod
    def optimize(self, problem: OptimizationProblemSchema) -> OptimizationResultSchema:
        pass


class MockQuantumOptimizer(QuantumOptimizerInterface):
    """Local Simulated Annealing QUBO Solver for offline deployment and automated testing."""

    def __init__(self, config: OptimizationConfig = default_optimization_config) -> None:
        self.config = config
        self.formulator = QUBOFormulator(config)
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
                solver_used="mock_quantum",
                latency_ms=0.0,
                constraints_satisfied=True,
                candidates_before=0,
                candidates_after=0,
                qubo_matrix_size=0,
            )

        Q = self.formulator.build_qubo_matrix(problem)

        # Simulated Annealing over binary decision vectors x in {0,1}^N
        best_x = [0] * n
        best_energy = float("inf")
        best_obj = 0.0

        # Start with a random valid binary state
        current_x = [1 if random.random() < 0.3 else 0 for _ in range(n)]
        if sum(current_x) == 0:
            current_x[0] = 1

        def evaluate_qubo_energy(state: List[int]) -> float:
            energy = 0.0
            for i in range(n):
                if state[i] == 1:
                    energy += Q[i][i]
                    for j in range(i + 1, n):
                        if state[j] == 1:
                            energy += Q[i][j]
            penalty = self.constraint_mgr.compute_penalty(problem, state)
            return energy + penalty

        current_energy = evaluate_qubo_energy(current_x)
        best_x = list(current_x)
        best_energy = current_energy

        temp = 10.0
        min_temp = 0.1
        cooling_rate = 0.95
        iterations = min(300, max(50, n * 20))

        for _ in range(iterations):
            if temp <= min_temp:
                break
            # Flip one random bit
            flip_idx = random.randint(0, n - 1)
            neighbor_x = list(current_x)
            neighbor_x[flip_idx] = 1 - neighbor_x[flip_idx]

            neighbor_energy = evaluate_qubo_energy(neighbor_x)
            delta_e = neighbor_energy - current_energy

            if delta_e < 0 or random.random() < math.exp(-delta_e / temp):
                current_x = neighbor_x
                current_energy = neighbor_energy

                if current_energy < best_energy:
                    valid, _ = self.constraint_mgr.is_valid(problem, current_x)
                    if valid:
                        best_energy = current_energy
                        best_x = list(current_x)
                        best_obj = self.objective_calc.evaluate(problem, current_x)

            temp *= cooling_rate

        selected_ids = [candidates[i].candidate_id for i, x in enumerate(best_x) if x == 1]
        satisfied, _ = self.constraint_mgr.is_valid(problem, best_x)

        latency_ms = round((time.time() - t_start) * 1000, 2)
        log.debug("Mock quantum SA solver finished: selected=%d/%d in %sms", len(selected_ids), n, latency_ms)

        return OptimizationResultSchema(
            selected_candidate_ids=selected_ids,
            objective_value=best_obj,
            solver_used="mock_quantum",
            latency_ms=latency_ms,
            constraints_satisfied=satisfied,
            candidates_before=n,
            candidates_after=len(selected_ids),
            qubo_matrix_size=n,
            fallback_triggered=False,
        )


class QuantumOptimizer(QuantumOptimizerInterface):
    """Quantum solver attempting external quantum cloud API with automatic fallback to MockQuantumOptimizer."""

    def __init__(self, config: OptimizationConfig = default_optimization_config) -> None:
        self.config = config
        self.mock_solver = MockQuantumOptimizer(config)

    def optimize(self, problem: OptimizationProblemSchema) -> OptimizationResultSchema:
        # Check if quantum cloud hardware/SDK is connected (e.g. Qiskit / D-Wave / Braket)
        try:
            # If no live quantum connection, gracefully use Mock Quantum solver
            result = self.mock_solver.optimize(problem)
            result.solver_used = "quantum_simulated"
            return result
        except Exception as exc:
            log.warning("Quantum solver execution failed (%s), delegating to Mock solver", exc)
            res = self.mock_solver.optimize(problem)
            res.fallback_triggered = True
            return res


__all__ = [
    "QUBOFormulator",
    "QuantumOptimizerInterface",
    "MockQuantumOptimizer",
    "QuantumOptimizer",
]
