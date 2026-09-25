"""Phase 11 Active Parameter Mechanism — Parameter Group Discovery & Strategy.

Discovers PyTorch model parameters and groups them logically into parameter groups
(e.g., layer1, layer2, classifier) based on naming patterns, depth, or custom strategies.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Union
import torch
import torch.nn as nn

from .schemas import ParameterGroupMetadata, ParameterInventory

log = logging.getLogger("gen-transform.active_params.groups")


class ParameterGroupingStrategy(ABC):
    """Abstract Base Class for grouping PyTorch model parameters logically."""

    @abstractmethod
    def group_parameters(
        self, model: nn.Module
    ) -> Dict[str, List[Tuple[str, nn.Parameter]]]:
        """Group named parameters into a mapping of group_name -> list of (param_name, parameter)."""
        pass


class PrefixParameterGroupingStrategy(ParameterGroupingStrategy):
    """Default grouping strategy based on parameter name prefix splitting."""

    def __init__(self, prefix_depth: int = 1, custom_mappings: Optional[Dict[str, str]] = None) -> None:
        self.prefix_depth = max(1, prefix_depth)
        self.custom_mappings = custom_mappings or {}

    def get_group_name(self, param_name: str) -> str:
        """Determine group name for a given parameter name key."""
        if param_name in self.custom_mappings:
            return self.custom_mappings[param_name]

        parts = param_name.split(".")
        if len(parts) == 1:
            return parts[0]

        # Handle common module prefix wrappers if present (e.g. module.fc1.weight -> fc1)
        if parts[0] in ("module", "model") and len(parts) > 2:
            parts = parts[1:]

        depth = min(self.prefix_depth, len(parts) - 1)
        return ".".join(parts[:depth])

    def group_parameters(
        self, model: nn.Module
    ) -> Dict[str, List[Tuple[str, nn.Parameter]]]:
        """Scan named parameters and partition into prefix-based groups."""
        groups: Dict[str, List[Tuple[str, nn.Parameter]]] = {}
        for name, param in model.named_parameters():
            group_name = self.get_group_name(name)
            if group_name not in groups:
                groups[group_name] = []
            groups[group_name].append((name, param))
        return groups


class ParameterGroupManager:
    """Manages parameter discovery, inventory generation, and group parameter access."""

    def __init__(self, strategy: Optional[ParameterGroupingStrategy] = None) -> None:
        self.strategy = strategy or PrefixParameterGroupingStrategy()

    def discover_groups(
        self, model: nn.Module, model_id: str = "model"
    ) -> ParameterInventory:
        """Scan model named parameters and construct typed ParameterInventory."""
        grouped_params = self.strategy.group_parameters(model)

        group_metadata_list: List[ParameterGroupMetadata] = []
        total_params = 0
        total_trainable = 0
        total_memory = 0

        for group_name, param_tuples in grouped_params.items():
            param_names = [t[0] for t in param_tuples]
            group_param_count = sum(p.numel() for _, p in param_tuples)
            group_trainable_count = sum(p.numel() for _, p in param_tuples if p.requires_grad)
            group_memory_bytes = sum(p.element_size() * p.numel() for _, p in param_tuples)

            active_state = any(p.requires_grad for _, p in param_tuples)

            group_meta = ParameterGroupMetadata(
                group_id=f"grp_{group_name}",
                group_name=group_name,
                parameter_names=param_names,
                parameter_count=group_param_count,
                trainable_parameter_count=group_trainable_count,
                estimated_memory_bytes=group_memory_bytes,
                active=active_state,
                score=1.0,
                importance=1.0,
                selection_reason="discovered",
            )
            group_metadata_list.append(group_meta)

            total_params += group_param_count
            total_trainable += group_trainable_count
            total_memory += group_memory_bytes

        inventory = ParameterInventory(
            model_id=model_id,
            total_parameters=total_params,
            trainable_parameters=total_trainable,
            total_memory_bytes=total_memory,
            groups=group_metadata_list,
        )
        return inventory

    def get_group_parameters(
        self, model: nn.Module, group_name: str
    ) -> List[Tuple[str, nn.Parameter]]:
        """Return parameter tuples belonging to specified group_name."""
        grouped_params = self.strategy.group_parameters(model)
        return grouped_params.get(group_name, [])


__all__ = [
    "ParameterGroupingStrategy",
    "PrefixParameterGroupingStrategy",
    "ParameterGroupManager",
]
