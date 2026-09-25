"""Phase 9 PyTorch Model Layer — Schemas.

Pydantic schemas for model metadata, loading requests, inference payloads,
latency metrics, and model status audits.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ModelMetadata(BaseModel):
    """Metadata describing a registered PyTorch model's state and specs."""

    model_id: str = Field(..., description="Unique model identifier")
    model_name: str = Field(..., description="Human-readable model name")
    model_type: str = Field("base", description="Model classification / role")
    version: str = Field("1.0.0", description="Model version")
    device: str = Field("cpu", description="Active device (cpu / cuda)")
    dtype: str = Field("float32", description="Tensor data type")
    parameter_count: int = Field(0, description="Total parameter count")
    trainable_parameter_count: int = Field(0, description="Trainable parameter count")
    loaded: bool = Field(False, description="True if loaded into memory")
    created_at: str = Field(..., description="Registration timestamp ISO string")
    status: str = Field("unloaded", description="Status: 'unloaded', 'loading', 'ready', 'error'")


class ModelLoadRequest(BaseModel):
    """Request payload to load a PyTorch model into registry."""

    model_id: str = Field(..., min_length=1)
    model_name: str = Field("PyTorch Model", min_length=1)
    model_type: str = Field("base")
    model_path: Optional[str] = Field(None)
    device: str = Field("auto")
    dtype: str = Field("float32")


class ModelInferenceRequest(BaseModel):
    """Request payload for model inference."""

    model_id: str = Field(..., min_length=1)
    inputs: Any = Field(..., description="Input tensor data or feature list")
    params: Dict[str, Any] = Field(default_factory=dict)


class ModelInferenceResponse(BaseModel):
    """Response payload returned after PyTorch model inference."""

    model_id: str
    outputs: Any = Field(..., description="Model predictions or output tensor data")
    latency_ms: float = Field(..., description="Inference latency in milliseconds")
    batch_size: int = Field(1)
    device_used: str = Field("cpu")


class ModelStatusResponse(BaseModel):
    """Response payload for model health/status checks."""

    ok: bool = True
    model_id: str
    metadata: ModelMetadata


__all__ = [
    "ModelMetadata",
    "ModelLoadRequest",
    "ModelInferenceRequest",
    "ModelInferenceResponse",
    "ModelStatusResponse",
]
