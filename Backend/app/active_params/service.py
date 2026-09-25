"""Phase 11 Active Parameter Mechanism — Service Layer Integration.

Integrates ActiveParameterController with Phase 9 ModelService and ModelRegistry,
enabling active parameter selection on registered models including Phase 10 distilled models.
"""

from __future__ import annotations

import logging
from typing import Optional

from ..models.service import ModelService, get_model_service
from .config import ActiveParamsSettings, get_active_params_settings
from .controller import ActiveParameterController
from .schemas import (
    ActiveParameterMetrics,
    ActiveParameterRequest,
    ActiveParameterResponse,
    ParameterInventory,
    SelectionStrategyEnum,
)

log = logging.getLogger("gen-transform.active_params.service")


class ActiveParameterService:
    """Service orchestrator managing active parameter selection and integration with Phase 9 ModelRegistry."""

    def __init__(
        self,
        model_service: Optional[ModelService] = None,
        controller: Optional[ActiveParameterController] = None,
        config: Optional[ActiveParamsSettings] = None,
    ) -> None:
        self.model_service = model_service or get_model_service()
        self.config = config or get_active_params_settings()
        self.controller = controller or ActiveParameterController(config=self.config)

    def select_parameters(self, request: ActiveParameterRequest) -> ActiveParameterResponse:
        """Execute active parameter selection on a registered PyTorch model."""
        model = self.model_service.registry.get(request.model_id)
        if model is None:
            raise KeyError(f"PyTorch model '{request.model_id}' is not registered in ModelRegistry.")

        return self.controller.execute_selection(model, request)

    def reset_model(self, model_id: str) -> ActiveParameterResponse:
        """Reset model parameters to all active / original snapshot state."""
        model = self.model_service.registry.get(model_id)
        if model is None:
            raise KeyError(f"PyTorch model '{model_id}' is not registered in ModelRegistry.")

        self.controller.reset(model, model_id=model_id)
        inventory = self.controller.discover(model, model_id=model_id)
        all_groups = [g.group_name for g in inventory.groups]

        return ActiveParameterResponse(
            model_id=model_id,
            selected_groups=all_groups,
            inactive_groups=[],
            active_parameter_count=inventory.total_parameters,
            total_parameter_count=inventory.total_parameters,
            active_ratio=1.0,
            scores={g.group_name: 1.0 for g in inventory.groups},
            strategy="reset",
            fallback_used=False,
            latency_ms=0.0,
            dry_run=False,
            details={"status": "reset_to_all_active"},
        )

    def get_inventory(self, model_id: str) -> ParameterInventory:
        """Retrieve ParameterInventory for a registered PyTorch model."""
        model = self.model_service.registry.get(model_id)
        if model is None:
            raise KeyError(f"PyTorch model '{model_id}' is not registered in ModelRegistry.")

        return self.controller.discover(model, model_id=model_id)

    def get_metrics(self, model_id: str) -> ActiveParameterMetrics:
        """Calculate and return ActiveParameterMetrics for a registered PyTorch model."""
        inventory = self.get_inventory(model_id)
        all_groups = [g.group_name for g in inventory.groups]

        # Calculate metrics assuming default active inventory
        scores = self.controller.score(
            self.model_service.registry.get(model_id), inventory
        )
        return self.controller.selector.config.enabled and ActiveParameterMetrics(
            total_parameters=inventory.total_parameters,
            active_parameters=inventory.trainable_parameters,
            inactive_parameters=inventory.total_parameters - inventory.trainable_parameters,
            active_ratio=(
                inventory.trainable_parameters / inventory.total_parameters
                if inventory.total_parameters > 0
                else 1.0
            ),
            total_memory_bytes=inventory.total_memory_bytes,
            active_memory_bytes=inventory.total_memory_bytes,
            selection_latency_ms=0.0,
            scoring_latency_ms=0.0,
            active_groups_count=len(inventory.groups),
            inactive_groups_count=0,
        )


_ACTIVE_PARAM_SERVICE_INSTANCE: Optional[ActiveParameterService] = None


def get_active_parameter_service() -> ActiveParameterService:
    """Return singleton instance of ActiveParameterService."""
    global _ACTIVE_PARAM_SERVICE_INSTANCE
    if _ACTIVE_PARAM_SERVICE_INSTANCE is None:
        _ACTIVE_PARAM_SERVICE_INSTANCE = ActiveParameterService()
    return _ACTIVE_PARAM_SERVICE_INSTANCE


def reset_active_parameter_service() -> None:
    """Reset singleton instance of ActiveParameterService."""
    global _ACTIVE_PARAM_SERVICE_INSTANCE
    _ACTIVE_PARAM_SERVICE_INSTANCE = None


__all__ = [
    "ActiveParameterService",
    "get_active_parameter_service",
    "reset_active_parameter_service",
]
