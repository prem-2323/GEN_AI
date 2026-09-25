"""Phase 10 Knowledge Distillation — Service Orchestrator.

Orchestrates complete Knowledge Distillation pipeline:
1. Validates configuration & Teacher-Student output dimension compatibility.
2. Retrieves Teacher & Student models from Phase 9 ModelRegistry.
3. Executes training loop via KnowledgeDistillationTrainer.
4. Evaluates performance comparison metrics via KnowledgeDistillationEvaluator.
5. Saves versioned student checkpoints via DistillationCheckpointManager.
6. Registers distilled Student model back into Phase 9 ModelRegistry.
"""
from __future__ import annotations

import time
import uuid
import logging
from typing import Any, Dict, List, Optional, Tuple
import torch
from torch.utils.data import DataLoader, Dataset


from ..models.base import BasePyTorchModel
from ..models.config import ModelConfig
from ..models.service import ModelService, get_model_service
from .checkpoint import DistillationCheckpointManager
from .config import DistillationConfig, default_distillation_config
from .data import SyntheticDistillationDataset, create_distillation_dataloader
from .evaluator import KnowledgeDistillationEvaluator
from .schemas import (
    DistillationComparison,
    DistillationMetrics,
    DistillationResult,
    DistillationStatusResponse,
)
from .student import StudentPyTorchModel
from .teacher import TeacherPyTorchModel
from .trainer import KnowledgeDistillationTrainer

log = logging.getLogger("gen-transform.distillation.service")


class KnowledgeDistillationService:
    """Orchestrates end-to-end Knowledge Distillation pipeline integrating Phase 9 Model Layer."""

    def __init__(self, model_service: Optional[ModelService] = None) -> None:
        self.model_svc = model_service or get_model_service()
        self.evaluator = KnowledgeDistillationEvaluator()
        self.checkpoint_mgr = DistillationCheckpointManager()

    def validate_compatibility(self, teacher: BasePyTorchModel, student: BasePyTorchModel) -> Tuple[bool, Optional[str]]:
        """Validate output logit dimensions between Teacher and Student models."""
        dummy_input = torch.zeros(1, 8, dtype=torch.float32).to(student.target_device)
        try:
            with torch.inference_mode():
                t_out = teacher(dummy_input.to(teacher.target_device))
                s_out = student(dummy_input)

            if t_out.shape != s_out.shape:
                reason = f"Logit shape mismatch: Teacher output shape {t_out.shape} != Student output shape {s_out.shape}."
                log.error("Distillation compatibility validation failed: %s", reason)
                return False, reason

            return True, None
        except Exception as exc:
            reason = f"Error during model output dry-run validation: {str(exc)}"
            log.error(reason)
            return False, reason

    def distill(
        self,
        config: Optional[DistillationConfig] = None,
        dataset: Optional[Dataset] = None,
    ) -> DistillationResult:
        """Execute complete Knowledge Distillation run."""
        t_start = time.time()
        job_id = f"distill_job_{uuid.uuid4().hex[:8]}"
        cfg = config or default_distillation_config

        log.info("Starting Knowledge Distillation job '%s' (Teacher='%s', Student='%s')", job_id, cfg.teacher_model_id, cfg.student_model_id)

        # 1. Retrieve or instantiate Teacher Model from Phase 9 Registry
        teacher = self.model_svc.registry.get(cfg.teacher_model_id)
        if teacher is None:
            log.info("Teacher '%s' not in registry; instantiating default TeacherPyTorchModel.", cfg.teacher_model_id)
            teacher = TeacherPyTorchModel(ModelConfig(model_id=cfg.teacher_model_id, model_name="Teacher Model", model_type="teacher", device=cfg.device))
            self.model_svc.register_model(teacher, replace=True)

        # 2. Retrieve or instantiate Student Model from Phase 9 Registry
        student = self.model_svc.registry.get(cfg.student_model_id)
        if student is None:
            log.info("Student '%s' not in registry; instantiating default StudentPyTorchModel.", cfg.student_model_id)
            student = StudentPyTorchModel(ModelConfig(model_id=cfg.student_model_id, model_name="Student Model", model_type="student", device=cfg.device))
            self.model_svc.register_model(student, replace=True)

        # 3. Validate Logit Dimensions Compatibility
        compatible, reason = self.validate_compatibility(teacher, student)
        if not compatible:
            duration = round(time.time() - t_start, 2)
            return DistillationResult(
                job_id=job_id,
                teacher_model_id=cfg.teacher_model_id,
                student_model_id=cfg.student_model_id,
                status="failed",
                epochs_completed=0,
                final_loss=0.0,
                duration_seconds=duration,
                error=reason,
            )

        # 4. Prepare Dataset & DataLoader
        ds = dataset or SyntheticDistillationDataset(num_samples=120, input_dim=8, num_classes=4, seed=42)
        dataloader = create_distillation_dataloader(ds, batch_size=cfg.batch_size, shuffle=True)

        # 5. Execute Distillation Training
        trainer = KnowledgeDistillationTrainer(
            teacher=teacher,
            student=student,
            dataloader=dataloader,
            config=cfg,
        )
        history = trainer.train()
        final_loss = history[-1]["total_loss"] if history else 0.0

        # 6. Evaluate Teacher vs Student Comparison
        eval_dataloader = create_distillation_dataloader(ds, batch_size=cfg.batch_size, shuffle=False)
        comparison = self.evaluator.compare(teacher=teacher, student=student, dataloader=eval_dataloader)

        # 7. Save Versioned Student Checkpoint
        metrics_dict = comparison.student_metrics.model_dump()
        checkpoint_path = self.checkpoint_mgr.save_checkpoint(
            student_model=student,
            optimizer=trainer.optimizer,
            config=cfg,
            epoch=cfg.epochs,
            metrics=metrics_dict,
        )

        # 8. Register Distilled Student Model in Phase 9 ModelRegistry
        distilled_model_id = f"distilled_{student.model_id}"
        distilled_config = ModelConfig(
            model_id=distilled_model_id,
            model_name=f"Distilled {student.model_name}",
            model_type="distilled",
            model_path=checkpoint_path,
            device=cfg.device,
        )
        student.config = distilled_config
        student.model_id = distilled_model_id
        student.model_type = "distilled"
        self.model_svc.register_model(student, replace=True)

        duration = round(time.time() - t_start, 2)

        log.info(
            "Distillation job '%s' finished successfully in %.2fs: registered distilled model '%s' (Param reduction: %.2f%%)",
            job_id,
            duration,
            distilled_model_id,
            comparison.parameter_reduction_percent,
        )

        return DistillationResult(
            job_id=job_id,
            teacher_model_id=cfg.teacher_model_id,
            student_model_id=student.model_id,
            status="completed",
            epochs_completed=cfg.epochs,
            final_loss=final_loss,
            comparison=comparison,
            checkpoint_path=checkpoint_path,
            registered_model_id=distilled_model_id,
            duration_seconds=duration,
        )


_DISTILLATION_SERVICE_INSTANCE: Optional[KnowledgeDistillationService] = None


def get_distillation_service() -> KnowledgeDistillationService:
    """Return singleton instance of KnowledgeDistillationService."""
    global _DISTILLATION_SERVICE_INSTANCE
    if _DISTILLATION_SERVICE_INSTANCE is None:
        _DISTILLATION_SERVICE_INSTANCE = KnowledgeDistillationService()
    return _DISTILLATION_SERVICE_INSTANCE


def reset_distillation_service() -> None:
    """Reset singleton distillation service instance."""
    global _DISTILLATION_SERVICE_INSTANCE
    _DISTILLATION_SERVICE_INSTANCE = None


__all__ = ["KnowledgeDistillationService", "get_distillation_service", "reset_distillation_service"]
