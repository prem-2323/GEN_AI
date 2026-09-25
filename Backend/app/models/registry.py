"""Phase 9 PyTorch Model Layer — Model Registry.

Provides thread-safe model registration, lookup, duplicate prevention, removal,
and metadata listing independent from RAG or external business logic.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from .base import BasePyTorchModel
from .schemas import ModelMetadata

log = logging.getLogger("gen-transform.models.registry")


class ModelRegistry:
    """Thread-safe registry maintaining active PyTorch model instances."""

    def __init__(self) -> None:
        self._models: Dict[str, BasePyTorchModel] = {}

    def register(self, model: BasePyTorchModel, replace: bool = False) -> bool:
        """Register a PyTorch model instance.

        Returns True on success. Raises ValueError on duplicate registration unless replace=True.
        """
        model_id = model.model_id
        if not model_id:
            raise ValueError("Model model_id cannot be empty.")

        if model_id in self._models and not replace:
            log.warning("Duplicate registration attempted for model_id '%s'", model_id)
            raise ValueError(f"Model '{model_id}' is already registered. Set replace=True to overwrite.")

        if model_id in self._models and replace:
            log.info("Overwriting existing registered model '%s'", model_id)
            old_model = self._models[model_id]
            old_model.unload()

        self._models[model_id] = model
        log.info("Registered PyTorch model '%s' (%s)", model_id, model.model_name)
        return True

    def get(self, model_id: str) -> Optional[BasePyTorchModel]:
        """Retrieve model instance by model_id."""
        return self._models.get(model_id)

    def remove(self, model_id: str) -> bool:
        """Remove model from registry and trigger unload."""
        if model_id in self._models:
            model = self._models.pop(model_id)
            model.unload()
            log.info("Removed model '%s' from registry.", model_id)
            return True
        return False

    def list_models(self) -> List[ModelMetadata]:
        """Return metadata snapshots for all registered models."""
        return [model.get_metadata() for model in self._models.values()]

    def has(self, model_id: str) -> bool:
        """Check if model_id is present in registry."""
        return model_id in self._models

    def clear(self) -> None:
        """Clear all registered models."""
        for model_id, model in list(self._models.items()):
            try:
                model.unload()
            except Exception:
                pass
        self._models.clear()
        log.info("Cleared all models from PyTorch ModelRegistry.")


__all__ = ["ModelRegistry"]
