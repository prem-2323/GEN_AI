"""Phase 11 Active Parameter Mechanism — Parameter Group Importance Scoring.

Calculates relevance/importance scores for parameter groups using parameter magnitude,
gradient magnitude, task/context relevance signals, and score normalization.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import torch
import torch.nn as nn

from .parameter_groups import ParameterGroupManager, PrefixParameterGroupingStrategy
from .schemas import ParameterInventory

log = logging.getLogger("gen-transform.active_params.scorer")


def normalize_scores(scores: Dict[str, float]) -> Dict[str, float]:
    """Normalize score values into range [0.0, 1.0]."""
    if not scores:
        return {}
    vals = list(scores.values())
    min_val, max_val = min(vals), max(vals)
    if max_val == min_val:
        return {k: 1.0 for k in scores}
    return {k: float((v - min_val) / (max_val - min_val)) for k, v in scores.items()}


class ParameterScorer(ABC):
    """Abstract Base Class for scoring parameter group importance."""

    @abstractmethod
    def score(
        self,
        model: nn.Module,
        inventory: ParameterInventory,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, float]:
        """Compute importance score for each parameter group in inventory."""
        pass


class ParameterMagnitudeScorer(ParameterScorer):
    """Scores parameter groups based on average parameter magnitude mean(abs(param))."""

    def __init__(self, use_squared: bool = False) -> None:
        self.use_squared = use_squared
        self.group_manager = ParameterGroupManager()

    def score(
        self,
        model: nn.Module,
        inventory: ParameterInventory,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, float]:
        scores: Dict[str, float] = {}
        for group in inventory.groups:
            params = self.group_manager.get_group_parameters(model, group.group_name)
            if not params:
                scores[group.group_name] = 0.0
                continue

            group_mags: List[float] = []
            with torch.no_grad():
                for _, p in params:
                    if p.numel() == 0:
                        continue
                    if self.use_squared:
                        mag = float(torch.mean(torch.square(p)).item())
                    else:
                        mag = float(torch.mean(torch.abs(p)).item())
                    group_mags.append(mag)

            scores[group.group_name] = (sum(group_mags) / len(group_mags)) if group_mags else 0.0

        return scores


class GradientImportanceScorer(ParameterScorer):
    """Scores parameter groups based on gradient magnitude mean(abs(grad)).

    Falls back cleanly to ParameterMagnitudeScorer if gradients are missing.
    """

    def __init__(self) -> None:
        self.magnitude_scorer = ParameterMagnitudeScorer()
        self.group_manager = ParameterGroupManager()

    def score(
        self,
        model: nn.Module,
        inventory: ParameterInventory,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, float]:
        has_grads = any(p.grad is not None for p in model.parameters())
        if not has_grads:
            log.debug("Gradients absent; GradientImportanceScorer falling back to magnitude scoring")
            return self.magnitude_scorer.score(model, inventory, context)

        scores: Dict[str, float] = {}
        for group in inventory.groups:
            params = self.group_manager.get_group_parameters(model, group.group_name)
            group_grad_mags: List[float] = []
            with torch.no_grad():
                for _, p in params:
                    if p.grad is not None and p.grad.numel() > 0:
                        g_mag = float(torch.mean(torch.abs(p.grad)).item())
                        group_grad_mags.append(g_mag)

            if group_grad_mags:
                scores[group.group_name] = sum(group_grad_mags) / len(group_grad_mags)
            else:
                # Fall back to magnitude score for this group if gradient is absent
                mag_score = self.magnitude_scorer.score(model, inventory, context)
                scores[group.group_name] = mag_score.get(group.group_name, 0.0)

        return scores


class ContextRelevanceScorer(ParameterScorer):
    """Scores parameter groups combining base magnitude with task/context affinity metadata."""

    # Deterministic task-to-group affinity weighting table
    TASK_AFFINITIES: Dict[str, Dict[str, float]] = {
        "classification": {"classifier": 2.0, "fc2": 1.8, "output": 2.0, "layer2": 1.3},
        "summarization": {"encoder": 1.8, "layer1": 1.5, "layer2": 1.5},
        "translation": {"layer1": 1.5, "layer2": 1.5, "fc1": 1.3},
        "report_generation": {"layer1": 1.4, "layer2": 1.6, "output": 1.5},
        "advisory": {"fc1": 1.5, "fc2": 1.5},
    }

    def __init__(self, base_scorer: Optional[ParameterScorer] = None) -> None:
        self.base_scorer = base_scorer or ParameterMagnitudeScorer()

    def score(
        self,
        model: nn.Module,
        inventory: ParameterInventory,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, float]:
        base_scores = self.base_scorer.score(model, inventory, context)
        if not context:
            return base_scores

        task_type = str(context.get("task_type", "")).lower()
        affinities = self.TASK_AFFINITIES.get(task_type, {})

        if not affinities:
            return base_scores

        adjusted_scores: Dict[str, float] = {}
        for group_name, base_score in base_scores.items():
            mult = 1.0
            for aff_key, aff_val in affinities.items():
                if aff_key in group_name.lower():
                    mult = max(mult, aff_val)
            adjusted_scores[group_name] = base_score * mult

        return adjusted_scores


__all__ = [
    "normalize_scores",
    "ParameterScorer",
    "ParameterMagnitudeScorer",
    "GradientImportanceScorer",
    "ContextRelevanceScorer",
]
