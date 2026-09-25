"""Phase 8 Quantum / Hybrid Optimization Module."""

from .config import OptimizationConfig, default_optimization_config
from .schemas import (
    CandidateFeatureVector,
    OptimizationMetadata,
    OptimizationProblemSchema,
    OptimizationResultSchema,
    OptimizationSelectRequest,
    OptimizationSelectResponse,
)
from .problem import ProblemFormulator
from .objective import ObjectiveCalculator
from .constraints import ConstraintManager
from .classical_solver import ClassicalOptimizer
from .quantum_solver import (
    QUBOFormulator,
    QuantumOptimizerInterface,
    MockQuantumOptimizer,
    QuantumOptimizer,
)
from .hybrid_solver import HybridOptimizer
from .service import OptimizationService, get_optimization_service, reset_optimization_service

__all__ = [
    "OptimizationConfig",
    "default_optimization_config",
    "CandidateFeatureVector",
    "OptimizationMetadata",
    "OptimizationProblemSchema",
    "OptimizationResultSchema",
    "OptimizationSelectRequest",
    "OptimizationSelectResponse",
    "ProblemFormulator",
    "ObjectiveCalculator",
    "ConstraintManager",
    "ClassicalOptimizer",
    "QUBOFormulator",
    "QuantumOptimizerInterface",
    "MockQuantumOptimizer",
    "QuantumOptimizer",
    "HybridOptimizer",
    "OptimizationService",
    "get_optimization_service",
    "reset_optimization_service",
]
