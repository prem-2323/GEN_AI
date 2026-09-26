"""Phase 6 QUBO Matrix Builder and Mathematical Objective Evaluation.

Implements min_x x^T Q x for candidate evidence subset selection.
"""
from __future__ import annotations

import math
import logging
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from .config import OptimizationConfig, default_optimization_config
from .schemas import CandidateFeatureVector

log = logging.getLogger("gen-transform.optimization.qubo_matrix")


class QUBOProblem(BaseModel):
    """Mathematical QUBO problem definition containing matrix Q and candidate metadata."""

    matrix: List[List[float]] = Field(..., description="N x N upper-triangular QUBO matrix Q")
    candidate_ids: List[str] = Field(..., description="Deterministic candidate IDs corresponding to row/col indices")
    candidates: List[CandidateFeatureVector] = Field(..., description="Feature vectors of input candidates")
    target_k: int = Field(..., description="Target candidate selection cardinality K")
    weights: Dict[str, float] = Field(..., description="Configured coefficient weights")
    constant_offset: float = Field(0.0, description="Constant offset C = P * K^2")
    representation: str = Field("upper_triangular", description="'upper_triangular' or 'symmetric'")
    feature_breakdown: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


def compute_pairwise_similarity(text1: str, text2: str) -> float:
    """Compute text similarity S_ij between two candidates using word Jaccard index."""
    if not text1 or not text2:
        return 0.0
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    if not words1 or not words2:
        return 0.0
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    return intersection / float(union) if union > 0 else 0.0


class QUBOFormulator:
    """Mathematical builder for Quadratic Unconstrained Binary Optimization matrix Q."""

    def __init__(self, config: OptimizationConfig = default_optimization_config) -> None:
        self.config = config

    def build_qubo(
        self,
        candidates: List[CandidateFeatureVector],
        target_k: Optional[int] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> QUBOProblem:
        """Formulate mathematically rigorous N x N QUBO matrix Q.

        Formula:
          E(x) = - alpha * sum(R_i * x_i)
                 - beta  * sum(G_i * x_i)
                 - gamma * sum(D_i * x_i)
                 + lambda * sum_{i<j}(S_ij * x_i * x_j)
                 + P * (sum(x_i) - K)^2

        Cardinality expansion:
          P * (sum(x_i) - K)^2 = P * sum( (1 - 2K)*x_i ) + 2P * sum_{i<j}(x_i * x_j) + P * K^2

        Matrix Coefficients (Upper Triangular):
          Q_ii = - alpha*R_i - beta*G_i - gamma*D_i + P*(1 - 2K)
          Q_ij = lambda * S_ij + 2P   (for i < j)
          Constant offset C = P * K^2
        """
        n = len(candidates)
        k = target_k if target_k is not None else self.config.default_target_k
        k = max(1, min(k, n if n > 0 else 1))

        # Resolve weights
        w = weights or {}
        alpha = float(w.get("relevance_weight", self.config.relevance_weight))
        beta = float(w.get("graph_weight", self.config.graph_weight))
        gamma = float(w.get("diversity_weight", self.config.diversity_weight))
        lam = float(w.get("redundancy_weight", self.config.redundancy_penalty))
        P = float(w.get("cardinality_penalty", self.config.cardinality_penalty))

        resolved_weights = {
            "relevance_weight": alpha,
            "graph_weight": beta,
            "diversity_weight": gamma,
            "redundancy_weight": lam,
            "cardinality_penalty": P,
        }

        if n == 0:
            return QUBOProblem(
                matrix=[],
                candidate_ids=[],
                candidates=[],
                target_k=k,
                weights=resolved_weights,
                constant_offset=0.0,
                representation="upper_triangular",
            )

        # Deterministic candidate ordering by candidate_id
        sorted_candidates = sorted(candidates, key=lambda c: c.candidate_id)
        candidate_ids = [c.candidate_id for c in sorted_candidates]

        Q = [[0.0] * n for _ in range(n)]

        # 1. Diagonal Terms Q_ii
        for i in range(n):
            cand = sorted_candidates[i]
            r_i = cand.relevance_score
            g_i = cand.graph_score
            d_i = cand.evidence_quality

            # Q_ii = - alpha*R_i - beta*G_i - gamma*D_i + P*(1 - 2K)
            Q[i][i] = (-alpha * r_i) + (-beta * g_i) + (-gamma * d_i) + P * (1.0 - 2.0 * float(k))

        # 2. Pairwise Off-Diagonal Terms Q_ij (i < j)
        for i in range(n):
            for j in range(i + 1, n):
                s_ij = compute_pairwise_similarity(sorted_candidates[i].text, sorted_candidates[j].text)
                # Extra document collision penalty if from same document
                if sorted_candidates[i].document_id == sorted_candidates[j].document_id:
                    s_ij = min(1.0, s_ij + 0.1)

                # Q_ij = lambda * S_ij + 2P
                Q[i][j] = (lam * s_ij) + (2.0 * P)

        constant_offset = P * (float(k) ** 2)

        feature_breakdown = {
            "n_candidates": n,
            "target_k": k,
            "constant_offset": constant_offset,
            "diag_sample": Q[0][0] if n > 0 else 0.0,
        }

        log.debug("Formulated QUBO matrix %dx%d for K=%d (offset=%.2f)", n, n, k, constant_offset)

        return QUBOProblem(
            matrix=Q,
            candidate_ids=candidate_ids,
            candidates=sorted_candidates,
            target_k=k,
            weights=resolved_weights,
            constant_offset=constant_offset,
            representation="upper_triangular",
            feature_breakdown=feature_breakdown,
        )

    def build_qubo_matrix(self, problem: Any) -> List[List[float]]:
        """Compatibility helper returning N x N matrix Q."""
        if hasattr(problem, "candidates"):
            candidates = problem.candidates
        else:
            candidates = problem
        qp = self.build_qubo(candidates)
        return qp.matrix


def qubo_energy(Q: List[List[float]], x: List[int], constant_offset: float = 0.0) -> float:
    """Calculate x^T Q x + constant_offset for binary solution vector x in {0,1}^N."""
    n = len(x)
    if n == 0 or not Q:
        return constant_offset

    energy = 0.0
    for i in range(n):
        if x[i] == 1:
            energy += Q[i][i]
            for j in range(i + 1, n):
                if x[j] == 1:
                    energy += Q[i][j]

    return energy + constant_offset


def evaluate_objective_breakdown(
    candidates: List[CandidateFeatureVector],
    x: List[int],
    target_k: int,
    weights: Dict[str, float],
) -> Dict[str, float]:
    """Decompose objective evaluation into physical component scores.

    Terms:
      - relevance_reward: - alpha * sum(R_i * x_i)
      - graph_reward:     - beta  * sum(G_i * x_i)
      - diversity_reward: - gamma * sum(D_i * x_i)
      - redundancy_penalty: + lambda * sum_{i<j}(S_ij * x_i * x_j)
      - cardinality_penalty: + P * (sum(x_i) - K)^2
      - total_energy: sum of terms
    """
    n = len(x)
    alpha = float(weights.get("relevance_weight", 1.0))
    beta = float(weights.get("graph_weight", 0.7))
    gamma = float(weights.get("diversity_weight", 0.4))
    lam = float(weights.get("redundancy_weight", 0.8))
    P = float(weights.get("cardinality_penalty", 2.0))

    rel_score = 0.0
    graph_score = 0.0
    div_score = 0.0
    red_score = 0.0

    selected_count = sum(x)

    for i in range(n):
        if x[i] == 1:
            rel_score += candidates[i].relevance_score
            graph_score += candidates[i].graph_score
            div_score += candidates[i].evidence_quality
            for j in range(i + 1, n):
                if x[j] == 1:
                    s_ij = compute_pairwise_similarity(candidates[i].text, candidates[j].text)
                    if candidates[i].document_id == candidates[j].document_id:
                        s_ij = min(1.0, s_ij + 0.1)
                    red_score += s_ij

    relevance_reward = -alpha * rel_score
    graph_reward = -beta * graph_score
    diversity_reward = -gamma * div_score
    redundancy_penalty = lam * red_score
    cardinality_penalty = P * float((selected_count - target_k) ** 2)

    total_energy = (
        relevance_reward
        + graph_reward
        + diversity_reward
        + redundancy_penalty
        + cardinality_penalty
    )

    return {
        "relevance_reward": round(relevance_reward, 4),
        "graph_reward": round(graph_reward, 4),
        "diversity_reward": round(diversity_reward, 4),
        "redundancy_penalty": round(redundancy_penalty, 4),
        "cardinality_penalty": round(cardinality_penalty, 4),
        "total_energy": round(total_energy, 4),
        "selected_count": selected_count,
        "target_k": target_k,
    }


__all__ = [
    "QUBOProblem",
    "QUBOFormulator",
    "qubo_energy",
    "evaluate_objective_breakdown",
    "compute_pairwise_similarity",
]
