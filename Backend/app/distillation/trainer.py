"""Phase 10 Knowledge Distillation — Training Engine.

Executes knowledge distillation training loops:
- Freezes Teacher PyTorch Model (`requires_grad = False`, `eval()` mode, `inference_mode()`)
- Trains Student PyTorch Model using temperature-scaled soft targets & hard labels
- Enforces gradient safety to guarantee Teacher parameters remain unchanged.
"""
from __future__ import annotations

import time
import logging
from typing import Dict, List, Optional, Tuple
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from ..models.base import BasePyTorchModel
from .config import DistillationConfig
from .losses import DistillationLoss

log = logging.getLogger("gen-transform.distillation.trainer")


class KnowledgeDistillationTrainer:
    """Orchestrates PyTorch knowledge distillation training loops."""

    def __init__(
        self,
        teacher: BasePyTorchModel,
        student: BasePyTorchModel,
        dataloader: DataLoader,
        config: DistillationConfig,
    ) -> None:
        self.teacher = teacher
        self.student = student
        self.dataloader = dataloader
        self.config = config
        self.device = student.target_device

        # Step 1: Freeze Teacher Model
        self.teacher.eval()
        for p in self.teacher.parameters():
            p.requires_grad = False

        # Step 2: Configure Student Optimizer
        self.optimizer = self._configure_optimizer()
        self.loss_fn = DistillationLoss(
            temperature=self.config.temperature,
            alpha=self.config.alpha,
        )

    def _configure_optimizer(self) -> torch.optim.Optimizer:
        opt_type = self.config.optimizer_type.lower()
        lr = self.config.learning_rate

        if opt_type == "adamw":
            return torch.optim.AdamW(self.student.parameters(), lr=lr)
        elif opt_type == "sgd":
            return torch.optim.SGD(self.student.parameters(), lr=lr, momentum=0.9)
        else:
            return torch.optim.Adam(self.student.parameters(), lr=lr)

    def train_epoch(self) -> Dict[str, float]:
        """Execute a single distillation training epoch over dataloader."""
        self.teacher.eval()
        self.student.train()

        total_loss_sum = 0.0
        distill_loss_sum = 0.0
        task_loss_sum = 0.0
        num_batches = 0

        # Capture initial snapshot of teacher weights for gradient safety check
        t_param_sample = [p.clone().detach() for p in self.teacher.parameters()][:1]

        self.optimizer.zero_grad()

        for step, batch in enumerate(self.dataloader, start=1):
            if isinstance(batch, (list, tuple)):
                inputs = batch[0].to(self.device)
                targets = batch[1].to(self.device) if len(batch) > 1 else None
            else:
                inputs = batch.to(self.device)
                targets = None

            # 1. Teacher Forward Pass (Frozen, Inference Mode)
            with torch.inference_mode():
                teacher_logits = self.teacher(inputs)

            # 2. Student Forward Pass (Trainable)
            student_logits = self.student(inputs)

            # 3. Compute Composite Distillation Loss
            total_loss, distill_loss, task_loss = self.loss_fn(
                student_logits=student_logits,
                teacher_logits=teacher_logits,
                targets=targets,
            )

            # Gradient accumulation scaling
            accum_loss = total_loss / self.config.gradient_accumulation_steps
            accum_loss.backward()

            if step % self.config.gradient_accumulation_steps == 0 or step == len(self.dataloader):
                # Gradient Clipping
                if self.config.max_grad_norm > 0.0:
                    nn.utils.clip_grad_norm_(self.student.parameters(), self.config.max_grad_norm)

                self.optimizer.step()
                self.optimizer.zero_grad()

            total_loss_sum += total_loss.item()
            distill_loss_sum += distill_loss.item()
            task_loss_sum += task_loss.item()
            num_batches += 1

        # Step 4: Gradient Safety Audit (Ensure Teacher parameters never changed)
        t_param_after = [p.clone().detach() for p in self.teacher.parameters()][:1]
        if t_param_sample and t_param_after:
            if not torch.equal(t_param_sample[0], t_param_after[0]):
                raise RuntimeError("CRITICAL GRADIENT SAFETY FAILURE: Teacher parameters were mutated during distillation!")

        avg_total = total_loss_sum / max(1, num_batches)
        avg_distill = distill_loss_sum / max(1, num_batches)
        avg_task = task_loss_sum / max(1, num_batches)

        return {
            "total_loss": float(round(avg_total, 4)),
            "distill_loss": float(round(avg_distill, 4)),
            "task_loss": float(round(avg_task, 4)),
            "learning_rate": self.optimizer.param_groups[0]["lr"],
        }

    def train(self) -> List[Dict[str, float]]:
        """Execute complete distillation training loop for configured epochs."""
        t_start = time.time()
        log.info(
            "Starting Knowledge Distillation: epochs=%d, T=%.2f, alpha=%.2f, lr=%s",
            self.config.epochs,
            self.config.temperature,
            self.config.alpha,
            self.config.learning_rate,
        )

        history: List[Dict[str, float]] = []
        for epoch in range(1, self.config.epochs + 1):
            epoch_metrics = self.train_epoch()
            epoch_metrics["epoch"] = epoch
            history.append(epoch_metrics)
            log.debug(
                "Epoch %d/%d: loss=%.4f (distill=%.4f, task=%.4f)",
                epoch,
                self.config.epochs,
                epoch_metrics["total_loss"],
                epoch_metrics["distill_loss"],
                epoch_metrics["task_loss"],
            )

        duration_ms = round((time.time() - t_start) * 1000, 2)
        log.info("Knowledge Distillation completed in %sms. Final loss: %.4f", duration_ms, history[-1]["total_loss"])
        return history


__all__ = ["KnowledgeDistillationTrainer"]
