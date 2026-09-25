"""Phase 11 Active Parameter Mechanism — Parameter Masking and Freezing.

Manages parameter activation states, setting requires_grad flags for gradient-level
freezing/unfreezing, providing safe state snapshotting, restoration, and weight integrity.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Set
import torch
import torch.nn as nn

from .parameter_groups import ParameterGroupManager
from .schemas import ParameterInventory

log = logging.getLogger("gen-transform.active_params.masking")


class ParameterMasker:
    """Manages gradient-level parameter masking, snapshot creation, and state restoration."""

    def __init__(self, group_manager: Optional[ParameterGroupManager] = None) -> None:
        self.group_manager = group_manager or ParameterGroupManager()

    def create_snapshot(self, model: nn.Module) -> Dict[str, bool]:
        """Record current requires_grad boolean state for every named parameter."""
        return {name: param.requires_grad for name, param in model.named_parameters()}

    def restore_snapshot(self, model: nn.Module, snapshot: Dict[str, bool]) -> None:
        """Restore exact original requires_grad state from snapshot."""
        param_dict = dict(model.named_parameters())
        for name, orig_grad in snapshot.items():
            if name in param_dict:
                param_dict[name].requires_grad = orig_grad
        log.debug("Restored original model parameter requires_grad states from snapshot")

    def apply_selection(
        self,
        model: nn.Module,
        selected_groups: List[str],
        inventory: ParameterInventory,
        freeze_inactive: bool = True,
    ) -> Dict[str, bool]:
        """Apply active/inactive selection by toggling requires_grad states.

        Returns snapshot of original state prior to application.
        """
        snapshot = self.create_snapshot(model)

        selected_set: Set[str] = set(selected_groups)
        grouped_params = self.group_manager.strategy.group_parameters(model)

        # Check if entire model is frozen (e.g., teacher model with requires_grad == False across all parameters)
        is_completely_frozen_model = all(not v for v in snapshot.values())

        for group_name, param_tuples in grouped_params.items():
            is_active = group_name in selected_set

            for name, param in param_tuples:
                orig_grad = snapshot.get(name, False)

                if is_active:
                    # Activate group: preserve original trainable state, but do NOT force teacher/frozen models to become trainable
                    if not is_completely_frozen_model:
                        param.requires_grad = True
                    else:
                        param.requires_grad = False
                else:
                    if freeze_inactive:
                        param.requires_grad = False

        return snapshot

    def verify_weight_integrity(
        self, original_weights: Dict[str, torch.Tensor], current_model: nn.Module
    ) -> bool:
        """Verify that parameter values (param.data) have not been modified or corrupted."""
        for name, param in current_model.named_parameters():
            if name in original_weights:
                if not torch.equal(param.data, original_weights[name]):
                    log.error("Weight corruption detected on parameter '%s'", name)
                    return False
        return True


__all__ = ["ParameterMasker"]
