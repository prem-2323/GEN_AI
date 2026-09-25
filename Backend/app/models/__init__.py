"""PyTorch Model Layer Module Boundary (Phase 9).

Provides clean abstractions for PyTorch model loading, registry management,
device placement (CPU/CUDA), gradient-free inference, and batch processing.

Domain schemas continue to be re-exported for backward compatibility.
"""
from __future__ import annotations

# Re-export domain models for backward compatibility
from ..domain_models import *
from ..domain_models import __all__ as _domain_all

# Phase 9 PyTorch Model Layer Abstractions
from .base import BasePyTorchModel, SimpleTestPyTorchModel
from .config import ModelConfig
from .device import DeviceManager
from .inference import InferenceEngine
from .loader import ModelLoader
from .registry import ModelRegistry
from .schemas import (
    ModelInferenceRequest,
    ModelInferenceResponse,
    ModelLoadRequest,
    ModelMetadata,
    ModelStatusResponse,
)
from .service import ModelService, get_model_service, reset_model_service

_pytorch_all = [
    "BasePyTorchModel",
    "SimpleTestPyTorchModel",
    "ModelConfig",
    "DeviceManager",
    "InferenceEngine",
    "ModelLoader",
    "ModelRegistry",
    "ModelMetadata",
    "ModelLoadRequest",
    "ModelInferenceRequest",
    "ModelInferenceResponse",
    "ModelStatusResponse",
    "ModelService",
    "get_model_service",
    "reset_model_service",
]

__all__ = list(_domain_all) + _pytorch_all
