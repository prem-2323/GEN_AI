"""Phase 11 — Active Parameter Mechanism Module.

Provides dynamic parameter discovery, logical grouping, importance scoring,
selection strategies, gradient masking/freezing, state restoration,
and integration with Phase 9 ModelService and Phase 10 Distillation models.
"""

from .config import ActiveParamsSettings, get_active_params_settings
from .controller import ActiveParameterController
from .masking import ParameterMasker
from .metrics import ActiveParameterMetricsCalculator
from .parameter_groups import ParameterGroupManager, PrefixParameterGroupingStrategy
from .schemas import (
    ActiveParameterConfigSchema,
    ActiveParameterMetrics,
    ActiveParameterRequest,
    ActiveParameterResponse,
    ParameterGroupMetadata,
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
from .selector import (
    AllParameterStrategy,
    BudgetParameterStrategy,
    ParameterSelectionStrategy,
    ParameterSelector,
    ThresholdParameterStrategy,
    TopKParameterStrategy,
)
from .service import ActiveParameterService, get_active_parameter_service, reset_active_parameter_service

__all__ = [
    "ActiveParamsSettings",
    "get_active_params_settings",
    "ActiveParameterController",
    "ParameterMasker",
    "ActiveParameterMetricsCalculator",
    "ParameterGroupManager",
    "PrefixParameterGroupingStrategy",
    "SelectionStrategyEnum",
    "ParameterGroupMetadata",
    "ParameterInventory",
    "ActiveParameterConfigSchema",
    "ActiveParameterRequest",
    "ActiveParameterResponse",
    "ActiveParameterMetrics",
    "ParameterScorer",
    "ParameterMagnitudeScorer",
    "GradientImportanceScorer",
    "ContextRelevanceScorer",
    "normalize_scores",
    "ParameterSelectionStrategy",
    "AllParameterStrategy",
    "TopKParameterStrategy",
    "ThresholdParameterStrategy",
    "BudgetParameterStrategy",
    "ParameterSelector",
    "ActiveParameterService",
    "get_active_parameter_service",
    "reset_active_parameter_service",
]
