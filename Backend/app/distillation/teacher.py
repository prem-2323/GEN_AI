"""Phase 10 Knowledge Distillation — Teacher Model Architecture.

Extends Phase 9 BasePyTorchModel to define a larger Teacher PyTorch Model.
"""
from __future__ import annotations

from typing import Any, List, Optional
import json
import logging
import torch
import torch.nn as nn

from ..models.base import BasePyTorchModel
from ..models.config import ModelConfig
from ..config.settings import get_settings
from .prompts import teacher_prompt

log = logging.getLogger("gen-transform.distillation.teacher")


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


def _valid_teacher_response(value: Any) -> bool:
    """Reject empty or schema-shaped-but-empty teacher responses."""
    return isinstance(value, dict) and bool(
        str(value.get("answer", "")).strip()
        and str(value.get("evidence", "")).strip()
    )


class OllamaTeacher:
    """Qwen teacher client used by the paper-QA distillation pipeline."""

    def __init__(self, model: Optional[str] = None, timeout: float = 180.0) -> None:
        self.model = model or get_settings().text_model
        self.timeout = timeout

    def _call(self, prompt: str) -> Optional[dict[str, Any]]:
        try:
            import ollama

            client = ollama.Client(host=get_settings().ollama_base_url, timeout=self.timeout)
            response = client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                format="json",
                options={"temperature": 0.0},
            )
            parsed = json.loads(response.get("message", {}).get("content", "").strip())
            return parsed if _valid_teacher_response(parsed) else None
        except Exception as exc:
            log.warning("Teacher call failed: %s", exc)
            return None

    def answer(self, question: str, evidence: str, pages: list[int]) -> Optional[dict[str, Any]]:
        result = self._call(teacher_prompt(question, evidence, pages))
        if result:
            return result
        return self._call(teacher_prompt(question, evidence[:1800], pages))


__all__ = ["TeacherPyTorchModel", "OllamaTeacher"]
