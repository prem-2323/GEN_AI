"""Phase 10 Knowledge Distillation — Schemas.

Pydantic schemas for training requests, loss/latency metrics, teacher vs student
performance comparisons, checkpoint records, and distillation status responses.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .config import DistillationConfig


class DistillationMetrics(BaseModel):
    """Measured performance metrics for a PyTorch model."""

    loss: float = Field(..., description="Overall loss value")
    distillation_loss: Optional[float] = Field(None, description="Soft-target KL divergence loss component")
    task_loss: Optional[float] = Field(None, description="Hard-label task loss component")
    accuracy: float = Field(0.0, description="Classification accuracy (0.0 to 1.0)")
    latency_ms: float = Field(..., description="Average inference latency in milliseconds")
    parameter_count: int = Field(..., description="Total model parameter count")
    model_size_kb: float = Field(..., description="Estimated model parameter size in KB")


class DistillationComparison(BaseModel):
    """Quantitative comparison between Teacher and Student PyTorch Models."""

    teacher_metrics: DistillationMetrics
    student_metrics: DistillationMetrics
    parameter_reduction_percent: float = Field(..., description="Percentage parameter reduction from teacher to student")
    latency_change_percent: float = Field(..., description="Percentage latency improvement/change")
    accuracy_delta: float = Field(..., description="Accuracy difference (Student - Teacher)")


class DistillationResult(BaseModel):
    """Final outcome payload for a Knowledge Distillation training execution."""

    job_id: str = Field(..., description="Unique distillation job ID")
    teacher_model_id: str
    student_model_id: str
    status: str = Field("completed", description="Status: 'completed', 'failed', 'running'")
    epochs_completed: int = Field(0)
    final_loss: float = Field(0.0)
    comparison: Optional[DistillationComparison] = None
    checkpoint_path: Optional[str] = None
    registered_model_id: Optional[str] = Field(None, description="Model ID under which distilled student was registered in Phase 9 ModelRegistry")
    duration_seconds: float = Field(0.0)
    error: Optional[str] = None


class DistillationRequest(BaseModel):
    """API request payload to trigger a Knowledge Distillation run."""

    teacher_model_id: str = Field("teacher_model_v1")
    student_model_id: str = Field("student_model_v1")
    config: Optional[DistillationConfig] = None
    project_id: Optional[str] = None
    source_id: Optional[str] = None
    pipeline: bool = False


class DistillationStatusResponse(BaseModel):
    """API status response for distillation job query."""

    job_id: str
    status: str
    progress: float = Field(1.0, ge=0.0, le=1.0)
    result: Optional[DistillationResult] = None


__all__ = [
    "DistillationMetrics",
    "DistillationComparison",
    "DistillationResult",
    "DistillationRequest",
    "DistillationStatusResponse",
]
