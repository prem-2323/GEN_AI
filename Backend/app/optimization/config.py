"""Phase 8 Quantum / Hybrid Optimization Configuration."""
from __future__ import annotations

from pydantic import BaseModel, Field


class OptimizationConfig(BaseModel):
    """Configuration parameters for Phase 8 evidence selection optimization."""

    enabled: bool = Field(True, description="Master switch for Phase 8 optimization layer")
    backend: str = Field(
        "hybrid",
        description="Optimization backend: 'classical', 'quantum', or 'hybrid'",
    )
    max_candidates: int = Field(50, ge=1, le=200, description="Max input candidates to consider")
    max_selected_candidates: int = Field(8, ge=1, le=50, description="Max candidates to select")
    max_context_tokens: int = Field(3000, ge=100, le=16000, description="Max context token budget")

    # Objective Function Weights
    relevance_weight: float = Field(0.40, ge=0.0, le=1.0, description="Weight for semantic relevance")
    graph_weight: float = Field(0.25, ge=0.0, le=1.0, description="Weight for graph structural relevance")
    diversity_weight: float = Field(0.15, ge=0.0, le=1.0, description="Weight for source document diversity")
    evidence_weight: float = Field(0.10, ge=0.0, le=1.0, description="Weight for evidence confidence score")
    redundancy_penalty: float = Field(0.15, ge=0.0, le=1.0, description="Penalty for pairwise text redundancy")
    cost_penalty: float = Field(0.05, ge=0.0, le=1.0, description="Penalty for token consumption")

    # QUBO Penalty Multipliers
    penalty_token_exceeded: float = Field(10.0, description="QUBO penalty multiplier for exceeding token budget")
    penalty_count_exceeded: float = Field(10.0, description="QUBO penalty multiplier for exceeding max selection count")


default_optimization_config = OptimizationConfig()

__all__ = ["OptimizationConfig", "default_optimization_config"]
