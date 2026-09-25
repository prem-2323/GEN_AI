"""Phase 13 Validation & Consistency Engine — Configuration Settings.

Defines validated configuration settings for fact validation, entity matching,
numeric strictness, citation validation, coverage thresholds, and decision policies.
"""

from __future__ import annotations

import logging
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

log = logging.getLogger("gen-transform.validation.config")


class ValidationSettings(BaseSettings):
    """Configuration settings for the Phase 13 Validation & Consistency Engine."""

    enabled: bool = Field(default=True, description="Enable Validation & Consistency Engine")
    strict_dates: bool = Field(default=True, description="Strict date mismatch detection (e.g. 2026-01-10 vs 2026-01-11)")
    strict_numbers: bool = Field(default=True, description="Strict numeric mismatch detection (e.g. 25m vs 250m)")
    strict_citations: bool = Field(default=True, description="Treat hallucinated citation IDs ([99]) as ERROR/CRITICAL")
    min_coverage_ratio: float = Field(default=0.7, description="Minimum acceptable evidence coverage ratio [0.0, 1.0]")
    default_policy: str = Field(default="FAIL_ON_CRITICAL", description="Decision policy: FAIL_ON_CRITICAL, FAIL_ON_ERROR, STRICT")
    enable_safe_formatting_repair: bool = Field(default=True, description="Enable safe non-factual formatting repair")
    allow_factual_auto_repair: bool = Field(default=False, description="CRITICAL: Never automatically rewrite factual values")
    deterministic_mode: bool = Field(default=True, description="Enforce deterministic validation rules")

    @field_validator("min_coverage_ratio")
    def validate_min_coverage(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"min_coverage_ratio must be in range [0.0, 1.0], got {v}")
        return v

    model_config = {
        "env_prefix": "VALIDATION_",
        "extra": "ignore",
    }


def get_validation_settings() -> ValidationSettings:
    """Instantiate and return ValidationSettings."""
    return ValidationSettings()


__all__ = ["ValidationSettings", "get_validation_settings"]
