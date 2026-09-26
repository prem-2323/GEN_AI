"""Phase 6 & 8 Real QUBO Evidence Selection Optimization Module."""

from .config import OptimizationConfig, default_optimization_config
from .qubo_matrix import (
    QUBOProblem,
    QUBOFormulator,
    qubo_energy,
    evaluate_objective_breakdown,
)
from .schemas import (
    CandidateFeatureVector,
    OptimizationMetadata,
    OptimizationProblemSchema,
    OptimizationResultSchema,
    OptimizationSelectRequest,
    OptimizationSelectResponse,
)
from .solvers import (
    QUBOOptimizationResult,
    QUBOSolver,
    ExactQUBOSolver,
    SimulatedAnnealingQUBOSolver,
    DWaveQUBOSolver,
    get_qubo_solver,
)
from .service import OptimizationService, get_optimization_service, reset_optimization_service

# Phase 8 Phase-specific exports
from .classical_solver import ClassicalOptimizer
from .constraints import ConstraintManager
from .hybrid_solver import HybridOptimizer
from .objective import ObjectiveCalculator
from .problem import ProblemFormulator
from .quantum_solver import MockQuantumOptimizer

__all__ = [
    "OptimizationConfig",
    "default_optimization_config",
    "QUBOProblem",
    "QUBOFormulator",
    "qubo_energy",
    "evaluate_objective_breakdown",
    "CandidateFeatureVector",
    "OptimizationMetadata",
    "OptimizationProblemSchema",
    "OptimizationResultSchema",
    "OptimizationSelectRequest",
    "OptimizationSelectResponse",
    "QUBOOptimizationResult",
    "QUBOSolver",
    "ExactQUBOSolver",
    "SimulatedAnnealingQUBOSolver",
    "DWaveQUBOSolver",
    "get_qubo_solver",
    "OptimizationService",
    "get_optimization_service",
    "reset_optimization_service",
    "ClassicalOptimizer",
    "ConstraintManager",
    "HybridOptimizer",
    "ObjectiveCalculator",
    "ProblemFormulator",
    "MockQuantumOptimizer",
]
