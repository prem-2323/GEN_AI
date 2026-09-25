"""Phase 10 Knowledge Distillation Module."""

from .config import DistillationConfig, PaperDistillationConfig, default_distillation_config
from .schemas import (
    DistillationComparison,
    DistillationMetrics,
    DistillationRequest,
    DistillationResult,
    DistillationStatusResponse,
)
from .losses import DistillationLoss
from .data import SyntheticDistillationDataset, create_distillation_dataloader
from .teacher import OllamaTeacher, TeacherPyTorchModel
from .student import StudentPyTorchModel
from .checkpoint import DistillationCheckpointManager
from .evaluator import KnowledgeDistillationEvaluator
from .trainer import KnowledgeDistillationTrainer
from .service import KnowledgeDistillationService, get_distillation_service, reset_distillation_service
from .dataset_generator import create_dataset, load_paper_context
from .train import inspect_runtime, run_qlora_training

__all__ = [
    "DistillationConfig",
    "PaperDistillationConfig",
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
    "OllamaTeacher",
    "StudentPyTorchModel",
    "DistillationCheckpointManager",
    "KnowledgeDistillationEvaluator",
    "KnowledgeDistillationTrainer",
    "KnowledgeDistillationService",
    "get_distillation_service",
    "reset_distillation_service",
    "create_dataset",
    "load_paper_context",
    "inspect_runtime",
    "run_qlora_training",
]
