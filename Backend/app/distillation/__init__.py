"""Phase 10 Knowledge Distillation Module."""

from .config import DistillationConfig, default_distillation_config
from .schemas import (
    DistillationComparison,
    DistillationMetrics,
    DistillationRequest,
    DistillationResult,
    DistillationStatusResponse,
)
from .losses import DistillationLoss
from .data import SyntheticDistillationDataset, create_distillation_dataloader
from .teacher import TeacherPyTorchModel
from .student import StudentPyTorchModel
from .checkpoint import DistillationCheckpointManager
from .evaluator import KnowledgeDistillationEvaluator
from .trainer import KnowledgeDistillationTrainer
from .service import KnowledgeDistillationService, get_distillation_service, reset_distillation_service

__all__ = [
    "DistillationConfig",
    "default_distillation_config",
    "DistillationComparison",
    "DistillationMetrics",
    "DistillationRequest",
    "DistillationResult",
    "DistillationStatusResponse",
    "DistillationLoss",
    "SyntheticDistillationDataset",
    "create_distillation_dataloader",
    "TeacherPyTorchModel",
    "StudentPyTorchModel",
    "DistillationCheckpointManager",
    "KnowledgeDistillationEvaluator",
    "KnowledgeDistillationTrainer",
    "KnowledgeDistillationService",
    "get_distillation_service",
    "reset_distillation_service",
]
