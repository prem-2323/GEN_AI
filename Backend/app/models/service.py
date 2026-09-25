"""Phase 9 PyTorch Model Layer — Service Orchestrator.

Orchestrates PyTorch model loading, registry management, device placement,
and inference execution for the ContentForge AI platform.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional

from .base import BasePyTorchModel, SimpleTestPyTorchModel
from .config import ModelConfig
from .device import DeviceManager
from .inference import InferenceEngine
from .loader import ModelLoader
from .registry import ModelRegistry
from .schemas import (
    ModelInferenceRequest,
    ModelInferenceResponse,
    ModelMetadata,
    ModelStatusResponse,
)

log = logging.getLogger("gen-transform.models.service")


class ModelService:
    """Orchestrates complete PyTorch model lifecycle, registry, and inference engine."""

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        loader: Optional[ModelLoader] = None,
    ) -> None:
        self.registry = registry or ModelRegistry()
        self.loader = loader or ModelLoader()
        self.inference_engine = InferenceEngine(self.registry)

        # Register default test model if registry is empty
        if not self.registry.list_models():
            test_model = SimpleTestPyTorchModel()
            self.registry.register(test_model, replace=True)

    def register_model(self, model: BasePyTorchModel, replace: bool = False) -> bool:
        """Register a PyTorch model instance directly."""
        return self.registry.register(model, replace=replace)

    def load_model(self, config: ModelConfig, replace: bool = True) -> ModelMetadata:
        """Load a PyTorch model via ModelLoader and register in ModelRegistry."""
        model = self.loader.load_model(config)
        self.registry.register(model, replace=replace)
        return model.get_metadata()

    def unload_model(self, model_id: str) -> bool:
        """Unload and remove a model from registry."""
        return self.registry.remove(model_id)

    def get_model_status(self, model_id: str) -> ModelStatusResponse:
        """Retrieve model status snapshot."""
        model = self.registry.get(model_id)
        if model is None:
            raise KeyError(f"PyTorch model '{model_id}' is not registered.")
        return ModelStatusResponse(ok=True, model_id=model_id, metadata=model.get_metadata())

    def list_models(self) -> List[ModelMetadata]:
        """List all registered PyTorch models and their metadata."""
        return self.registry.list_models()

    def predict(self, model_id: str, inputs: Any, params: Optional[dict] = None) -> ModelInferenceResponse:
        """Execute single inference on a registered model."""
        req = ModelInferenceRequest(model_id=model_id, inputs=inputs, params=params or {})
        return self.inference_engine.run_inference(req)

    def predict_batch(self, model_id: str, inputs: List[Any], params: Optional[dict] = None) -> ModelInferenceResponse:
        """Execute batch inference on a registered model."""
        req = ModelInferenceRequest(model_id=model_id, inputs=inputs, params=params or {})
        return self.inference_engine.run_inference(req)

    def get_device_info(self) -> dict:
        """Return host system PyTorch device diagnostics."""
        return DeviceManager.get_device_info()


_MODEL_SERVICE_INSTANCE: Optional[ModelService] = None


def get_model_service() -> ModelService:
    """Return singleton instance of ModelService."""
    global _MODEL_SERVICE_INSTANCE
    if _MODEL_SERVICE_INSTANCE is None:
        _MODEL_SERVICE_INSTANCE = ModelService()
    return _MODEL_SERVICE_INSTANCE


def reset_model_service() -> None:
    """Reset singleton model service instance."""
    global _MODEL_SERVICE_INSTANCE
    _MODEL_SERVICE_INSTANCE = None


__all__ = ["ModelService", "get_model_service", "reset_model_service"]
