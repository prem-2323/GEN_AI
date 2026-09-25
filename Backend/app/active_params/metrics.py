"""Phase 11 Active Parameter Mechanism — Metrics Calculation.

Computes parameter counts, active ratio, memory footprints, and latency metrics
for active parameter groups and execution audit reports.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from .schemas import ActiveParameterMetrics, ParameterInventory

log = logging.getLogger("gen-transform.active_params.metrics")


class ActiveParameterMetricsCalculator:
    """Calculates operational and efficiency metrics for parameter selection."""

    @staticmethod
    def compute_metrics(
        inventory: ParameterInventory,
        selected_groups: List[str],
        scores: Dict[str, float],
        selection_latency_ms: float = 0.0,
        scoring_latency_ms: float = 0.0,
        baseline_latency_ms: Optional[float] = None,
        active_policy_latency_ms: Optional[float] = None,
    ) -> ActiveParameterMetrics:
        """Compute typed ActiveParameterMetrics from inventory and selection results."""
        selected_set = set(selected_groups)

        total_params = inventory.total_parameters
        total_memory = inventory.total_memory_bytes

        active_params = 0
        active_memory = 0
        active_groups_count = 0
        inactive_groups_count = 0

        for group in inventory.groups:
            if group.group_name in selected_set:
                active_params += group.parameter_count
                active_memory += group.estimated_memory_bytes
                active_groups_count += 1
            else:
                inactive_groups_count += 1

        inactive_params = total_params - active_params
        active_ratio = (active_params / total_params) if total_params > 0 else 1.0

        return ActiveParameterMetrics(
            total_parameters=total_params,
            active_parameters=active_params,
            inactive_parameters=inactive_params,
            active_ratio=float(round(active_ratio, 6)),
            total_memory_bytes=total_memory,
            active_memory_bytes=active_memory,
            selection_latency_ms=float(round(selection_latency_ms, 3)),
            scoring_latency_ms=float(round(scoring_latency_ms, 3)),
            active_groups_count=active_groups_count,
            inactive_groups_count=inactive_groups_count,
            baseline_latency_ms=baseline_latency_ms,
            active_policy_latency_ms=active_policy_latency_ms,
        )


__all__ = ["ActiveParameterMetricsCalculator"]
