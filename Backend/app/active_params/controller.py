"""Phase 11 Active Parameter Mechanism — Controller Orchestrator.

Orchestrates parameter group discovery, importance scoring, selection strategies,
dry-run preview, state application, snapshot restoration, and metrics generation.
"""

from __future__ import annotations

import time
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
import torch
import torch.nn as nn

from ..models.base import BasePyTorchModel
from .config import ActiveParamsSettings, get_active_params_settings
from .masking import ParameterMasker
from .metrics import ActiveParameterMetricsCalculator
from .parameter_groups import ParameterGroupManager
from .schemas import (
    ActiveParameterRequest,
    ActiveParameterResponse,
    ParameterInventory,
    SelectionStrategyEnum,
)
from .scorer import (
    ContextRelevanceScorer,
    GradientImportanceScorer,
    ParameterMagnitudeScorer,
    ParameterScorer,
    normalize_scores,
)
from .selector import ParameterSelector

log = logging.getLogger("gen-transform.active_params.controller")


class ActiveParameterController:
    """Controller managing the full lifecycle of parameter selection, activation, and state restoration."""

    def __init__(
        self,
        config: Optional[ActiveParamsSettings] = None,
        group_manager: Optional[ParameterGroupManager] = None,
        scorer: Optional[ParameterScorer] = None,
        selector: Optional[ParameterSelector] = None,
        masker: Optional[ParameterMasker] = None,
    ) -> None:
        self.config = config or get_active_params_settings()
        self.group_manager = group_manager or ParameterGroupManager()
        self.magnitude_scorer = ParameterMagnitudeScorer()
        self.gradient_scorer = GradientImportanceScorer()
        self.context_scorer = ContextRelevanceScorer(self.magnitude_scorer)
        self.scorer = scorer or self.magnitude_scorer
        self.selector = selector or ParameterSelector(self.config)
        self.masker = masker or ParameterMasker(self.group_manager)
        self._model_snapshots: Dict[str, Dict[str, bool]] = {}

    def discover(self, model: nn.Module, model_id: str = "model") -> ParameterInventory:
        """Inspect model and build ParameterInventory."""
        return self.group_manager.discover_groups(model, model_id=model_id)

    def score(
        self,
        model: nn.Module,
        inventory: ParameterInventory,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, float]:
        """Compute importance scores for parameter groups in inventory."""
        # Determine appropriate scorer based on context and gradient state
        has_grads = any(p.grad is not None for p in model.parameters())
        if context and (context.get("task_type") or context.get("input_metadata")):
            active_scorer = self.context_scorer
        elif has_grads:
            active_scorer = self.gradient_scorer
        else:
            active_scorer = self.magnitude_scorer

        raw_scores = active_scorer.score(model, inventory, context)

        if self.config.score_normalization:
            return normalize_scores(raw_scores)
        return raw_scores

    def select(
        self,
        inventory: ParameterInventory,
        scores: Dict[str, float],
        request: Optional[ActiveParameterRequest] = None,
    ) -> Tuple[List[str], bool]:
        """Select parameter group names according to requested or configured policy."""
        return self.selector.select(inventory, scores, request)

    def apply(
        self,
        model: nn.Module,
        selected_groups: List[str],
        inventory: ParameterInventory,
        model_id: str = "model",
    ) -> Dict[str, bool]:
        """Apply active/inactive selection by adjusting parameter requires_grad state.

        Saves original snapshot for restoration.
        """
        snapshot = self.masker.apply_selection(
            model,
            selected_groups,
            inventory,
            freeze_inactive=self.config.freeze_inactive,
        )
        self._model_snapshots[model_id] = snapshot
        log.info(
            "Applied parameter selection for model '%s': active groups=%s",
            model_id,
            selected_groups,
        )
        return snapshot

    def reset(self, model: nn.Module, model_id: str = "model") -> bool:
        """Reset model parameters to original requires_grad state from saved snapshot."""
        snapshot = self._model_snapshots.get(model_id)
        if snapshot:
            self.masker.restore_snapshot(model, snapshot)
            log.info("Reset parameter state for model '%s'", model_id)
            return True
        else:
            # Fallback reset: set all parameters to trainable (if not teacher)
            for p in model.parameters():
                p.requires_grad = True
            log.info("Fallback reset: enabled requires_grad for all parameters of '%s'", model_id)
            return False

    def execute_selection(
        self,
        model: Union[nn.Module, BasePyTorchModel],
        request: ActiveParameterRequest,
    ) -> ActiveParameterResponse:
        """Full pipeline execution: discover -> score -> select -> (apply) -> response."""
        start_time = time.perf_counter()
        model_id = request.model_id or getattr(model, "model_id", "model")

        # 1. Discover parameter inventory
        inventory = self.discover(model, model_id=model_id)

        # 2. Score parameter groups
        scoring_start = time.perf_counter()
        context_data: Dict[str, Any] = {}
        if request.task_type:
            context_data["task_type"] = request.task_type
        if request.input_metadata:
            context_data["input_metadata"] = request.input_metadata

        scores = self.score(model, inventory, context=context_data if context_data else None)
        scoring_latency_ms = (time.perf_counter() - scoring_start) * 1000.0

        # 3. Select active groups
        selection_start = time.perf_counter()
        selected_groups, fallback_used = self.select(inventory, scores, request)
        selection_latency_ms = (time.perf_counter() - selection_start) * 1000.0

        all_group_names = [g.group_name for g in inventory.groups]
        selected_set = set(selected_groups)
        inactive_groups = [name for name in all_group_names if name not in selected_set]

        # 4. Apply selection if not dry-run
        if not request.dry_run:
            self.apply(model, selected_groups, inventory, model_id=model_id)

        # 5. Calculate metrics
        metrics = ActiveParameterMetricsCalculator.compute_metrics(
            inventory=inventory,
            selected_groups=selected_groups,
            scores=scores,
            selection_latency_ms=selection_latency_ms,
            scoring_latency_ms=scoring_latency_ms,
        )

        total_latency_ms = (time.perf_counter() - start_time) * 1000.0

        used_strategy = (
            request.strategy.value if request.strategy else self.config.selection_strategy
        )

        return ActiveParameterResponse(
            model_id=model_id,
            selected_groups=selected_groups,
            inactive_groups=inactive_groups,
            active_parameter_count=metrics.active_parameters,
            total_parameter_count=metrics.total_parameters,
            active_ratio=metrics.active_ratio,
            scores=scores,
            strategy=used_strategy,
            fallback_used=fallback_used,
            latency_ms=round(total_latency_ms, 3),
            dry_run=request.dry_run,
            details={
                "scoring_latency_ms": metrics.scoring_latency_ms,
                "selection_latency_ms": metrics.selection_latency_ms,
                "total_memory_bytes": metrics.total_memory_bytes,
                "active_memory_bytes": metrics.active_memory_bytes,
                "freeze_inactive": self.config.freeze_inactive,
            },
        )


__all__ = ["ActiveParameterController"]
