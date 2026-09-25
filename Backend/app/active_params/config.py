"""Phase 11 Active Parameter Mechanism — Configuration Settings.

Defines validated configuration settings for parameter group selection strategies,
thresholds, resource budgets, and safety fallbacks.
"""

from __future__ import annotations

import logging
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

log = logging.getLogger("gen-transform.active_params.config")


class ActiveParamsSettings(BaseSettings):
    """Configuration settings for the Active Parameter Mechanism."""

    enabled: bool = Field(default=True, description="Enable active parameter selection mechanism")
    selection_strategy: str = Field(default="top_k", description="Selection strategy: 'all', 'top_k', 'threshold', 'budget'")
    threshold: float = Field(default=0.5, description="Normalized score threshold for activation [0.0, 1.0]")
    top_k: int = Field(default=2, description="Top-k active parameter groups count (>0)")
    minimum_active_groups: int = Field(default=1, description="Minimum parameter groups that must remain active (>=1)")
    maximum_active_groups: Optional[int] = Field(default=None, description="Maximum active parameter groups ceiling")
    max_active_parameter_count: Optional[int] = Field(default=None, description="Maximum parameter count budget")
    max_active_memory: Optional[int] = Field(default=None, description="Maximum memory bytes budget")
    fallback_to_all: bool = Field(default=True, description="Fallback to safe activation if selection returns empty")
    freeze_inactive: bool = Field(default=True, description="Freeze gradients (requires_grad=False) for inactive groups")
    score_normalization: bool = Field(default=True, description="Normalize group scores to range [0.0, 1.0]")
    deterministic_mode: bool = Field(default=True, description="Enforce deterministic scoring and selection")

    @field_validator("selection_strategy")
    def validate_selection_strategy(cls, v: str) -> str:
        valid_strategies = {"all", "top_k", "threshold", "budget"}
        v_lower = v.lower()
        if v_lower not in valid_strategies:
            raise ValueError(f"Invalid selection_strategy '{v}'. Must be one of {sorted(valid_strategies)}")
        return v_lower

    @field_validator("threshold")
    def validate_threshold(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"threshold must be in range [0.0, 1.0], got {v}")
        return v

    @field_validator("top_k")
    def validate_top_k(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"top_k must be > 0, got {v}")
        return v

    @field_validator("minimum_active_groups")
    def validate_min_groups(cls, v: int) -> int:
        if v < 1:
            raise ValueError(f"minimum_active_groups must be >= 1, got {v}")
        return v

    @field_validator("maximum_active_groups")
    def validate_max_groups(cls, v: Optional[int], info) -> Optional[int]:
        if v is not None:
            min_g = info.data.get("minimum_active_groups", 1)
            if v < min_g:
                raise ValueError(f"maximum_active_groups ({v}) cannot be less than minimum_active_groups ({min_g})")
        return v

    model_config = {
        "env_prefix": "ACTIVE_PARAMS_",
        "extra": "ignore",
    }


def get_active_params_settings() -> ActiveParamsSettings:
    """Instantiate and return ActiveParamsSettings."""
    return ActiveParamsSettings()


__all__ = ["ActiveParamsSettings", "get_active_params_settings"]
