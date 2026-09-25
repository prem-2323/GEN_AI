"""Phase 10 Knowledge Distillation — Teacher Model Architecture.

Extends Phase 9 BasePyTorchModel to define a larger Teacher PyTorch Model.
"""
from __future__ import annotations

from typing import Any, List, Optional
import torch
import torch.nn as nn

from ..models.base import BasePyTorchModel
from ..models.config import ModelConfig


class TeacherPyTorchModel(BasePyTorchModel):
    """Larger Teacher PyTorch Model architecture with multiple dense hidden layers."""

    def __init__(self, config: Optional[ModelConfig] = None) -> None:
        cfg = config or ModelConfig(
            model_id="teacher_model_v1",
            model_name="Teacher Model (32-16 Hidden)",
            model_type="teacher",
        )
        super().__init__(cfg)
        self.fc1 = nn.Linear(8, 32)
        self.relu1 = nn.ReLU()
        self.fc2 = nn.Linear(32, 16)
        self.relu2 = nn.ReLU()
        self.fc3 = nn.Linear(16, 4)
        self.initialize()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.fc1(x)
        out = self.relu1(out)
        out = self.fc2(out)
        out = self.relu2(out)
        out = self.fc3(out)
        return out

    def predict(self, inputs: Any) -> List[float]:
        if isinstance(inputs, list):
            tensor_in = torch.tensor(inputs, dtype=torch.float32)
        elif isinstance(inputs, torch.Tensor):
            tensor_in = inputs
        else:
            tensor_in = torch.ones(8, dtype=torch.float32)

        if tensor_in.ndim == 1:
            tensor_in = tensor_in.unsqueeze(0)

        tensor_in = tensor_in.to(self.target_device)
        with torch.inference_mode():
            output = self.forward(tensor_in)

        return output.squeeze(0).cpu().tolist()

    def predict_batch(self, inputs: List[Any]) -> List[List[float]]:
        if not inputs:
            return []

        tensor_in = torch.tensor(inputs, dtype=torch.float32).to(self.target_device)
        with torch.inference_mode():
            outputs = self.forward(tensor_in)

        return outputs.cpu().tolist()


__all__ = ["TeacherPyTorchModel"]
