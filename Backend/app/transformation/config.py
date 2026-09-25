"""Phase 12 Transformation Engine — Configuration Settings.

Defines configuration settings for transformation profiles, model adapters,
fact preservation rules, and citation strictness.
"""

from __future__ import annotations

import logging
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

log = logging.getLogger("gen-transform.transformation.config")


class TransformationSettings(BaseSettings):
    """Configuration settings for the Phase 12 Transformation Engine."""

    enabled: bool = Field(default=True, description="Enable Transformation Engine")
    default_output_type: str = Field(default="SUMMARY", description="Default transformation output type")
    default_tone: str = Field(default="PROFESSIONAL", description="Default tone")
    default_audience: str = Field(default="GENERAL_PUBLIC", description="Default audience")
    default_detail_level: str = Field(default="MEDIUM", description="Default detail level")
    default_language: str = Field(default="en", description="Default source/target language")
    preserve_facts: bool = Field(default=True, description="Enforce strict factual preservation rules")
    strict_citations: bool = Field(default=True, description="Enforce strict citation matching against evidence")
    allow_insufficient_evidence: bool = Field(default=True, description="Return structured insufficient-evidence response instead of hallucinating")
    max_context_length: int = Field(default=8192, description="Maximum character context length for prompt construction")
    default_model_id: str = Field(default="default_pytorch_model", description="Default PyTorch model ID")
    default_model_type: str = Field(default="standard", description="Default model type (standard, distilled, external)")
    deterministic_fallback: bool = Field(default=True, description="Use deterministic rule-based generator fallback when model is unavailable")

    @field_validator("max_context_length")
    def validate_max_context_length(cls, v: int) -> int:
        if v < 256:
            raise ValueError(f"max_context_length must be >= 256, got {v}")
        return v

    model_config = {
        "env_prefix": "TRANSFORMATION_",
        "extra": "ignore",
    }


def get_transformation_settings() -> TransformationSettings:
    """Instantiate and return TransformationSettings."""
    return TransformationSettings()


__all__ = ["TransformationSettings", "get_transformation_settings"]
