"""Phase 8 Quantum / Hybrid Optimization — Objective Function.

Evaluates multi-objective utility for candidate subsets:
Relevance + Graph Coverage + Source Diversity + Evidence Quality - Redundancy - Context Cost.
"""
from __future__ import annotations

import logging
from typing import List, Set

from .config import OptimizationConfig, default_optimization_config
from .schemas import CandidateFeatureVector, OptimizationProblemSchema

log = logging.getLogger("gen-transform.optimization.objective")


class ObjectiveCalculator:
    """Computes composite multi-objective score for candidate binary selection vector X."""

    def __init__(self, config: OptimizationConfig = default_optimization_config) -> None:
        self.config = config

    def evaluate(
        self,
        problem: OptimizationProblemSchema,
        selection: List[int],
    ) -> float:
        """Compute objective score for binary selection vector selection (e.g. [1, 0, 1, 1])."""
        candidates = problem.candidates
        n = len(candidates)
        if len(selection) != n or sum(selection) == 0:
            return 0.0

        selected_indices = [i for i, x in enumerate(selection) if x == 1]
        k = len(selected_indices)

        # 1. Relevance Score Component (Normalized average of selected relevance)
        rel_sum = sum(candidates[i].relevance_score for i in selected_indices)
        relevance_score = rel_sum / k

        # 2. Graph Coverage Component (Ratio of selected items that contain graph evidence)
        graph_count = sum(1 for i in selected_indices if candidates[i].source_type == "graph")
        graph_coverage = min(1.0, graph_count / max(1, min(k, 3)))

        # 3. Source Document Diversity (Ratio of distinct document IDs)
        doc_ids: Set[str] = {candidates[i].document_id for i in selected_indices}
        diversity_score = len(doc_ids) / max(1, k)

        # 4. Evidence Quality (Average evidence confidence)
        ev_sum = sum(candidates[i].evidence_quality for i in selected_indices)
        evidence_quality = ev_sum / k

        # 5. Redundancy Penalty (Pairwise overlap sum between selected candidates)
        redundancy_penalty_sum = 0.0
        if k > 1 and problem.pairwise_redundancy_matrix:
            matrix = problem.pairwise_redundancy_matrix
            pair_count = 0
            for idx_a in range(len(selected_indices)):
                for idx_b in range(idx_a + 1, len(selected_indices)):
                    i = selected_indices[idx_a]
                    j = selected_indices[idx_b]
                    redundancy_penalty_sum += matrix[i][j]
                    pair_count += 1
            if pair_count > 0:
                redundancy_penalty_sum /= pair_count

        # 6. Context Cost Penalty (Normalized total token usage)
        total_tokens = sum(candidates[i].token_cost for i in selected_indices)
        cost_ratio = min(1.0, total_tokens / max(1, problem.max_context_tokens))

        # Composite Objective Computation
        w_rel = self.config.relevance_weight
        w_graph = self.config.graph_weight
        w_div = self.config.diversity_weight
        w_ev = self.config.evidence_weight
        w_red = self.config.redundancy_penalty
        w_cost = self.config.cost_penalty

        raw_score = (
            w_rel * relevance_score
            + w_graph * graph_coverage
            + w_div * diversity_score
            + w_ev * evidence_quality
            - w_red * redundancy_penalty_sum
            - w_cost * cost_ratio
        )

        return float(round(max(0.0, raw_score), 4))


__all__ = ["ObjectiveCalculator"]
