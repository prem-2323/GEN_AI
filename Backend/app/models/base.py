"""Phase 9 PyTorch Model Layer — Base Model Abstraction.

Defines BasePyTorchModel abstract interface extending torch.nn.Module, supporting
initialization, device placement, weight loading, inference, parameter counting,
metadata extraction, and a deterministic SimpleTestPyTorchModel for rapid testing.
"""
from __future__ import annotations

import time
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import torch
import torch.nn as nn

from ..utils.helpers import utcnow_iso
from .config import ModelConfig
from .device import DeviceManager
from .schemas import ModelMetadata

log = logging.getLogger("gen-transform.models.base")


class BasePyTorchModel(nn.Module, ABC):
    """Abstract Base Class for all PyTorch models in ContentForge AI backend."""

    def __init__(self, config: Optional[ModelConfig] = None) -> None:
        super().__init__()
        self.config = config or ModelConfig(model_id="base_model", model_name="Base Model")
        self.model_id = self.config.model_id
        self.model_name = self.config.model_name
        self.model_type = self.config.model_type
        self.version = self.config.version
        self.target_device = DeviceManager.get_device(self.config.device)
        self.is_loaded = False
        self.created_at = utcnow_iso()

    def initialize(self) -> None:
        """Initialize model components and move weights to target device."""
        self.to_device(self.target_device)
        self.eval()
        self.is_loaded = True
        log.info("Initialized PyTorch model '%s' (%s) on device '%s'", self.model_id, self.model_name, self.target_device)

    def to_device(self, device: torch.device) -> BasePyTorchModel:
        """Move model to specified PyTorch device."""
        self.target_device = device
        self.to(device)
        return self

    def get_parameter_count(self) -> int:
        """Return total number of parameters."""
        return sum(p.numel() for p in self.parameters())

    def get_trainable_parameter_count(self) -> int:
        """Return total number of trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def get_metadata(self) -> ModelMetadata:
        """Return typed ModelMetadata audit snapshot."""
        return ModelMetadata(
            model_id=self.model_id,
            model_name=self.model_name,
            model_type=self.model_type,
            version=self.version,
            device=str(self.target_device),
            dtype=self.config.dtype,
            parameter_count=self.get_parameter_count(),
            trainable_parameter_count=self.get_trainable_parameter_count(),
            loaded=self.is_loaded,
            created_at=self.created_at,
            status="ready" if self.is_loaded else "unloaded",
        )

    def load_weights(self, checkpoint_path: str) -> bool:
        """Load state_dict weights from filesystem checkpoint path safely."""
        try:
            state_dict = torch.load(checkpoint_path, map_location=self.target_device)
            if isinstance(state_dict, dict) and "state_dict" in state_dict:
                state_dict = state_dict["state_dict"]
            self.load_state_dict(state_dict)
            self.eval()
            self.is_loaded = True
            log.info("Successfully loaded PyTorch weights for '%s' from '%s'", self.model_id, checkpoint_path)
            return True
        except Exception as exc:
            log.error("Failed to load state_dict for '%s' from '%s': %s", self.model_id, checkpoint_path, exc)
            return False

    def unload(self) -> None:
        """Release model weights and reset status."""
        self.is_loaded = False
        log.info("Unloaded PyTorch model '%s'", self.model_id)


    @abstractmethod
    def predict(self, inputs: Any) -> Any:
        """Execute inference on a single input tensor/sample."""
        pass

    @abstractmethod
    def predict_batch(self, inputs: List[Any]) -> List[Any]:
        """Execute inference on a batch of input samples."""
        pass


class SimpleTestPyTorchModel(BasePyTorchModel):
    """Deterministic, lightweight PyTorch model for testing infrastructure without external downloads."""

    def __init__(self, config: Optional[ModelConfig] = None) -> None:
        cfg = config or ModelConfig(
            model_id="test_linear_v1",
            model_name="Simple Test Linear Model",
            model_type="test_linear",
        )
        super().__init__(cfg)
        self.fc1 = nn.Linear(8, 16)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(16, 4)
        self.initialize()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.fc1(x)
        out = self.relu(out)
        out = self.fc2(out)
        return out

    def predict(self, inputs: Any) -> List[float]:
        """Execute prediction on a single 8-dim float vector or list."""
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
        """Execute prediction on a batch of 8-dim float vectors."""
        if not inputs:
            return []

        tensor_in = torch.tensor(inputs, dtype=torch.float32).to(self.target_device)
        with torch.inference_mode():
            outputs = self.forward(tensor_in)

        return outputs.cpu().tolist()


__all__ = ["BasePyTorchModel", "SimpleTestPyTorchModel"]
