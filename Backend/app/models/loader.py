"""Phase 9 PyTorch Model Layer — Model Loader.

Provides safe model loading, state_dict checkpoint validation, device placement,
and model caching to prevent redundant model reloads.
"""
from __future__ import annotations

import logging
from typing import Dict, Optional, Type
import torch

from .base import BasePyTorchModel, SimpleTestPyTorchModel
from .config import ModelConfig
from .device import DeviceManager

log = logging.getLogger("gen-transform.models.loader")

_MODEL_CLASS_REGISTRY: Dict[str, Type[BasePyTorchModel]] = {
    "test_linear": SimpleTestPyTorchModel,
    "base": SimpleTestPyTorchModel,
}


class ModelLoader:
    """Handles PyTorch model loading, checkpoint weight validation, and device placement."""

    def __init__(self) -> None:
        self.cache: Dict[str, BasePyTorchModel] = {}


    @staticmethod
    def register_model_class(model_type: str, model_cls: Type[BasePyTorchModel]) -> None:
        """Register a PyTorch model class for instantiation by model_type."""
        _MODEL_CLASS_REGISTRY[model_type.lower()] = model_cls
        log.info("Registered PyTorch model class '%s' for type '%s'", model_cls.__name__, model_type)

    def load_model(self, config: ModelConfig, force_reload: bool = False) -> BasePyTorchModel:
        """Instantiate and load PyTorch model based on config."""
        model_id = config.model_id
        if not force_reload and model_id in self.cache:
            log.debug("Returning cached PyTorch model instance for '%s'", model_id)
            return self.cache[model_id]

        target_device = DeviceManager.get_device(config.device)
        model_type = config.model_type.lower()

        model_cls = _MODEL_CLASS_REGISTRY.get(model_type, SimpleTestPyTorchModel)
        log.info("Instantiating PyTorch model class '%s' for model_id '%s'", model_cls.__name__, model_id)

        try:
            model = model_cls(config)
            model.to_device(target_device)
            model.eval()

            # Load checkpoint if path provided
            if config.model_path:
                model.load_weights(config.model_path)
            else:
                model.is_loaded = True

            self.cache[model_id] = model
            return model
        except Exception as exc:
            log.exception("Failed to load PyTorch model '%s': %s", model_id, exc)
            raise RuntimeError(f"Failed to load PyTorch model '{model_id}': {str(exc)}") from exc

    def clear_cache(self) -> None:
        """Clear loaded model cache."""
        self.cache.clear()
        log.info("Cleared PyTorch model loader cache.")


__all__ = ["ModelLoader"]
