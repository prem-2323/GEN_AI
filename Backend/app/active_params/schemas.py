"""Phase 11 Active Parameter Mechanism — Pydantic Schemas.

Defines API and internal schemas for parameter group inventories, requests, responses,
configurations, and execution metrics without exposing raw PyTorch tensor objects.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class SelectionStrategyEnum(str, Enum):
    """Supported parameter group selection strategies."""

    ALL = "all"
    TOP_K = "top_k"
    THRESHOLD = "threshold"
    BUDGET = "budget"


class ParameterGroupMetadata(BaseModel):
    """Metadata audit record for a single logical parameter group."""

    group_id: str = Field(description="Unique identifier for the parameter group")
    group_name: str = Field(description="Human-readable group name (e.g., 'layer1', 'fc1')")
    parameter_names: List[str] = Field(default_factory=list, description="List of PyTorch named parameter keys in group")
    parameter_count: int = Field(default=0, description="Total number of elements/weights in group")
    trainable_parameter_count: int = Field(default=0, description="Total trainable elements in group")
    estimated_memory_bytes: int = Field(default=0, description="Estimated memory footprint in bytes")
    active: bool = Field(default=True, description="Whether group is active for computation/gradients")
    score: float = Field(default=1.0, description="Calculated importance score for the group")
    importance: float = Field(default=1.0, description="Normalized group importance score [0.0, 1.0]")
    selection_reason: str = Field(default="default", description="Rationale for group activation/deactivation")


class ParameterInventory(BaseModel):
    """Complete parameter inventory snapshot for a PyTorch model."""

    model_id: str = Field(description="Target PyTorch model identifier")
    total_parameters: int = Field(default=0, description="Total parameter count across all groups")
    trainable_parameters: int = Field(default=0, description="Total trainable parameters across all groups")
    total_memory_bytes: int = Field(default=0, description="Total estimated memory footprint in bytes")
    groups: List[ParameterGroupMetadata] = Field(default_factory=list, description="Logical parameter groups")


class ActiveParameterConfigSchema(BaseModel):
    """Configuration schema for parameter selection execution."""

    enabled: bool = Field(default=True)
    strategy: SelectionStrategyEnum = Field(default=SelectionStrategyEnum.TOP_K)
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    top_k: int = Field(default=2, gt=0)
    minimum_active_groups: int = Field(default=1, ge=1)
    maximum_active_groups: Optional[int] = Field(default=None)
    parameter_budget: Optional[int] = Field(default=None)
    memory_budget: Optional[int] = Field(default=None)
    fallback_to_all: bool = Field(default=True)
    freeze_inactive: bool = Field(default=True)
    score_normalization: bool = Field(default=True)
    deterministic_mode: bool = Field(default=True)


class ActiveParameterRequest(BaseModel):
    """Request payload to select active parameter groups on a model."""

    model_id: str = Field(description="Target model identifier registered in ModelRegistry")
    task_type: Optional[str] = Field(default=None, description="Optional task type context (e.g. 'summarization')")
    input_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional input payload metadata")
    strategy: Optional[SelectionStrategyEnum] = Field(default=None, description="Override selection strategy")
    threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Override score threshold")
    top_k: Optional[int] = Field(default=None, gt=0, description="Override top_k count")
    parameter_budget: Optional[int] = Field(default=None, description="Override parameter count ceiling")
    memory_budget: Optional[int] = Field(default=None, description="Override memory bytes ceiling")
    dry_run: bool = Field(default=False, description="If True, calculate selection without modifying model state")


class ActiveParameterResponse(BaseModel):
    """Response payload detailing active parameter selection results."""

    model_id: str = Field(description="Target model identifier")
    selected_groups: List[str] = Field(default_factory=list, description="List of activated group names")
    inactive_groups: List[str] = Field(default_factory=list, description="List of deactivated/frozen group names")
    active_parameter_count: int = Field(default=0, description="Active parameter count")
    total_parameter_count: int = Field(default=0, description="Total parameter count")
    active_ratio: float = Field(default=1.0, description="Ratio of active parameters (active / total)")
    scores: Dict[str, float] = Field(default_factory=dict, description="Importance scores per group")
    strategy: str = Field(description="Strategy used for selection")
    fallback_used: bool = Field(default=False, description="Whether fallback policy was triggered")
    latency_ms: float = Field(default=0.0, description="Scoring & selection latency in milliseconds")
    dry_run: bool = Field(default=False, description="Whether this response was a dry run")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional audit metadata")


class ActiveParameterMetrics(BaseModel):
    """Resource and timing metrics for active parameter selection."""

    total_parameters: int = Field(default=0)
    active_parameters: int = Field(default=0)
    inactive_parameters: int = Field(default=0)
    active_ratio: float = Field(default=1.0)
    total_memory_bytes: int = Field(default=0)
    active_memory_bytes: int = Field(default=0)
    selection_latency_ms: float = Field(default=0.0)
    scoring_latency_ms: float = Field(default=0.0)
    active_groups_count: int = Field(default=0)
    inactive_groups_count: int = Field(default=0)
    baseline_latency_ms: Optional[float] = Field(default=None)
    active_policy_latency_ms: Optional[float] = Field(default=None)


__all__ = [
    "SelectionStrategyEnum",
    "ParameterGroupMetadata",
    "ParameterInventory",
    "ActiveParameterConfigSchema",
    "ActiveParameterRequest",
    "ActiveParameterResponse",
    "ActiveParameterMetrics",
]
