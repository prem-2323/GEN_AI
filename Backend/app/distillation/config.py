"""Phase 10 Knowledge Distillation — Configuration.

Defines validated configuration parameters for transferring knowledge from a Teacher PyTorch Model
to a smaller Student PyTorch Model using temperature-scaled soft targets and hard-label task losses.
"""
from __future__ import annotations

import os
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class DistillationConfig(BaseModel):
    """Validated configuration for Knowledge Distillation training."""

    teacher_model_id: str = Field("teacher_model_v1", min_length=1, description="Registered teacher model ID")
    student_model_id: str = Field("student_model_v1", min_length=1, description="Target student model ID")
    temperature: float = Field(4.0, gt=0.0, description="Softmax temperature scaling parameter (T > 0.0)")
    alpha: float = Field(0.7, ge=0.0, le=1.0, description="Weighting factor for distillation loss (0.0 to 1.0)")
    learning_rate: float = Field(1e-3, gt=0.0, description="Learning rate for student model optimizer")
    epochs: int = Field(5, ge=1, le=100, description="Number of distillation training epochs")
    batch_size: int = Field(16, ge=1, le=256, description="Training batch size")
    gradient_accumulation_steps: int = Field(1, ge=1, le=64, description="Gradient accumulation steps")
    max_grad_norm: float = Field(1.0, ge=0.0, description="Maximum gradient clipping norm")
    optimizer_type: str = Field("adam", description="Student optimizer: 'adam', 'adamw', or 'sgd'")
    scheduler_type: str = Field("none", description="Learning rate scheduler: 'none', 'linear', or 'step'")
    device: str = Field("auto", description="Execution device: 'auto', 'cpu', or 'cuda'")
    checkpoint_dir: str = Field("./storage/checkpoints/distillation", description="Directory to save student checkpoints")
    eval_frequency: int = Field(1, ge=1, description="Evaluate every N epochs")

    @model_validator(mode="after")
    def validate_distillation_params(self) -> DistillationConfig:
        if self.temperature <= 0.0:
            raise ValueError("Temperature must be strictly greater than 0.0")
        if not (0.0 <= self.alpha <= 1.0):
            raise ValueError("Alpha must be between 0.0 and 1.0 inclusive")
        return self


default_distillation_config = DistillationConfig()

__all__ = ["DistillationConfig", "default_distillation_config"]
