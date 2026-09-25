"""Phase 11 Active Parameter Mechanism — Parameter Selection Strategies.

Implements selection strategies (ALL, TOP_K, THRESHOLD, BUDGET) with minimum active group
guarantees, maximum group ceilings, resource budget enforcement, and safety fallbacks.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

from .config import ActiveParamsSettings
from .schemas import ActiveParameterRequest, ParameterInventory, SelectionStrategyEnum

log = logging.getLogger("gen-transform.active_params.selector")


class ParameterSelectionStrategy(ABC):
    """Abstract Base Class for parameter group selection strategies."""

    @abstractmethod
    def select(
        self,
        inventory: ParameterInventory,
        scores: Dict[str, float],
        config: ActiveParamsSettings,
        request: Optional[ActiveParameterRequest] = None,
    ) -> Tuple[List[str], bool]:
        """Select group names to activate and return (selected_group_names, fallback_used)."""
        pass


class AllParameterStrategy(ParameterSelectionStrategy):
    """Selects all parameter groups in the model."""

    def select(
        self,
        inventory: ParameterInventory,
        scores: Dict[str, float],
        config: ActiveParamsSettings,
        request: Optional[ActiveParameterRequest] = None,
    ) -> Tuple[List[str], bool]:
        return [g.group_name for g in inventory.groups], False


class TopKParameterStrategy(ParameterSelectionStrategy):
    """Selects top K groups ranked by importance score."""

    def select(
        self,
        inventory: ParameterInventory,
        scores: Dict[str, float],
        config: ActiveParamsSettings,
        request: Optional[ActiveParameterRequest] = None,
    ) -> Tuple[List[str], bool]:
        top_k = (request.top_k if request and request.top_k is not None else config.top_k)
        top_k = max(1, top_k)

        sorted_groups = sorted(
            inventory.groups,
            key=lambda g: scores.get(g.group_name, 0.0),
            reverse=True,
        )
        selected = [g.group_name for g in sorted_groups[:top_k]]
        return selected, False


class ThresholdParameterStrategy(ParameterSelectionStrategy):
    """Selects parameter groups with score >= threshold."""

    def select(
        self,
        inventory: ParameterInventory,
        scores: Dict[str, float],
        config: ActiveParamsSettings,
        request: Optional[ActiveParameterRequest] = None,
    ) -> Tuple[List[str], bool]:
        thresh = (request.threshold if request and request.threshold is not None else config.threshold)

        selected = [
            g.group_name
            for g in inventory.groups
            if scores.get(g.group_name, 0.0) >= thresh
        ]
        return selected, False


class BudgetParameterStrategy(ParameterSelectionStrategy):
    """Selects highest scoring groups within parameter count or memory budget."""

    def select(
        self,
        inventory: ParameterInventory,
        scores: Dict[str, float],
        config: ActiveParamsSettings,
        request: Optional[ActiveParameterRequest] = None,
    ) -> Tuple[List[str], bool]:
        param_budget = (
            request.parameter_budget
            if request and request.parameter_budget is not None
            else config.max_active_parameter_count
        )
        mem_budget = (
            request.memory_budget
            if request and request.memory_budget is not None
            else config.max_active_memory
        )

        sorted_groups = sorted(
            inventory.groups,
            key=lambda g: scores.get(g.group_name, 0.0),
            reverse=True,
        )

        selected: List[str] = []
        curr_params = 0
        curr_mem = 0

        for g in sorted_groups:
            would_exceed_params = (param_budget is not None and (curr_params + g.parameter_count > param_budget))
            would_exceed_mem = (mem_budget is not None and (curr_mem + g.estimated_memory_bytes > mem_budget))

            if selected and (would_exceed_params or would_exceed_mem):
                continue

            selected.append(g.group_name)
            curr_params += g.parameter_count
            curr_mem += g.estimated_memory_bytes

        return selected, False


class ParameterSelector:
    """Orchestrates strategy execution, budget enforcement, and safe minimum group fallbacks."""

    def __init__(self, config: Optional[ActiveParamsSettings] = None) -> None:
        self.config = config or ActiveParamsSettings()
        self.strategies: Dict[str, ParameterSelectionStrategy] = {
            "all": AllParameterStrategy(),
            "top_k": TopKParameterStrategy(),
            "threshold": ThresholdParameterStrategy(),
            "budget": BudgetParameterStrategy(),
        }

    def select(
        self,
        inventory: ParameterInventory,
        scores: Dict[str, float],
        request: Optional[ActiveParameterRequest] = None,
    ) -> Tuple[List[str], bool]:
        """Execute selection with safety bounds and minimum active group guarantees."""
        if not inventory.groups:
            return [], False

        strat_key = (
            request.strategy.value.lower()
            if request and request.strategy is not None
            else self.config.selection_strategy.lower()
        )
        strategy = self.strategies.get(strat_key, self.strategies["top_k"])

        selected_groups, fallback_used = strategy.select(inventory, scores, self.config, request)

        min_groups = self.config.minimum_active_groups
        max_groups = self.config.maximum_active_groups

        # Safe minimum active groups fallback
        if len(selected_groups) < min_groups:
            log.warning(
                "Selection strategy '%s' selected %d groups (< min %d); falling back to top %d groups",
                strat_key,
                len(selected_groups),
                min_groups,
                min_groups,
            )
            sorted_groups = sorted(
                inventory.groups,
                key=lambda g: scores.get(g.group_name, 0.0),
                reverse=True,
            )
            selected_groups = [g.group_name for g in sorted_groups[:min_groups]]
            fallback_used = True

        # Enforce maximum active groups ceiling
        if max_groups is not None and len(selected_groups) > max_groups:
            selected_groups = selected_groups[:max_groups]

        return selected_groups, fallback_used


__all__ = [
    "ParameterSelectionStrategy",
    "AllParameterStrategy",
    "TopKParameterStrategy",
    "ThresholdParameterStrategy",
    "BudgetParameterStrategy",
    "ParameterSelector",
]
