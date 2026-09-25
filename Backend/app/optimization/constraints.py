"""Phase 8 Quantum / Hybrid Optimization — Constraint Manager.

Enforces hard token and selection count boundaries, and constructs QUBO quadratic constraint penalties.
"""
from __future__ import annotations

import logging
from typing import List, Tuple

from .config import OptimizationConfig, default_optimization_config
from .schemas import OptimizationProblemSchema

log = logging.getLogger("gen-transform.optimization.constraints")


class ConstraintManager:
    """Validates selection vector constraints and computes penalty terms."""

    def __init__(self, config: OptimizationConfig = default_optimization_config) -> None:
        self.config = config

    def is_valid(
        self,
        problem: OptimizationProblemSchema,
        selection: List[int],
    ) -> Tuple[bool, List[str]]:
        """Audit whether selection vector X satisfies all hard constraints."""
        candidates = problem.candidates
        if not candidates:
            return True, []

        selected_indices = [i for i, x in enumerate(selection) if x == 1]
        violations: List[str] = []

        # Constraint 1: Minimum selection
        if len(selected_indices) == 0:
            violations.append("Selection set is empty.")

        # Constraint 2: Maximum selection count
        if len(selected_indices) > problem.max_selected_candidates:
            violations.append(
                f"Selected candidates count ({len(selected_indices)}) exceeds max limit ({problem.max_selected_candidates})."
            )

        # Constraint 3: Maximum context token budget
        total_tokens = sum(candidates[i].token_cost for i in selected_indices)
        if total_tokens > problem.max_context_tokens:
            violations.append(
                f"Total token cost ({total_tokens}) exceeds max context token budget ({problem.max_context_tokens})."
            )

        satisfied = len(violations) == 0
        return satisfied, violations

    def compute_penalty(
        self,
        problem: OptimizationProblemSchema,
        selection: List[int],
    ) -> float:
        """Compute quadratic penalty score for QUBO formulation when constraints are breached."""
        candidates = problem.candidates
        selected_indices = [i for i, x in enumerate(selection) if x == 1]

        # Count overflow penalty
        count_excess = max(0, len(selected_indices) - problem.max_selected_candidates)
        count_penalty = self.config.penalty_count_exceeded * (count_excess ** 2)

        # Token overflow penalty
        total_tokens = sum(candidates[i].token_cost for i in selected_indices)
        token_excess_ratio = max(0.0, (total_tokens - problem.max_context_tokens) / max(1, problem.max_context_tokens))
        token_penalty = self.config.penalty_token_exceeded * (token_excess_ratio ** 2)

        # Empty selection penalty
        empty_penalty = 100.0 if len(selected_indices) == 0 else 0.0

        return count_penalty + token_penalty + empty_penalty


__all__ = ["ConstraintManager"]
