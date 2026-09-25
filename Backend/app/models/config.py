"""Phase 9 PyTorch Model Layer — Configuration.

Defines Pydantic configuration schemas for PyTorch models, device preferences,
batching parameters, and inference timeouts.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    """Configuration parameters for loading and executing a PyTorch model."""

    model_id: str = Field(..., min_length=1, description="Unique model identifier")
    model_name: str = Field(..., min_length=1, description="Human readable model name")
    model_type: str = Field(
        "base",
        description="Model architecture/role: 'base', 'teacher', 'student', 'distilled', 'classifier', 'text_encoder', 'text_generator', 'reranker', or 'test_linear'",
    )
    model_path: Optional[str] = Field(None, description="Local filesystem path to model checkpoint/state_dict")
    pretrained_source: Optional[str] = Field(None, description="Pretrained model identifier or repository name")
    device: str = Field("auto", description="Preferred device: 'auto', 'cpu', 'cuda', 'cuda:0'")
    dtype: str = Field("float32", description="PyTorch tensor dtype: 'float32', 'float16', 'bfloat16'")
    batch_size: int = Field(16, ge=1, le=512, description="Max batch size for inference")
    max_sequence_length: int = Field(512, ge=1, le=8192, description="Max token sequence length")
    inference_timeout: float = Field(30.0, ge=0.1, le=600.0, description="Inference execution timeout in seconds")
    version: str = Field("1.0.0", description="Model version string")
    enabled: bool = Field(True, description="Enabled status flag")


__all__ = ["ModelConfig"]
