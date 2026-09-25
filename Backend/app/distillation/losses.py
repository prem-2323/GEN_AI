"""Phase 10 Knowledge Distillation — Loss Functions.

Implements standard Knowledge Distillation Loss combining temperature-scaled soft-target
KL divergence with hard-label task loss: L_total = alpha * L_distillation + (1 - alpha) * L_task.
"""
from __future__ import annotations

import logging
from typing import Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F

log = logging.getLogger("gen-transform.distillation.losses")


class DistillationLoss(nn.Module):
    """Computes temperature-scaled KL divergence distillation loss and hard-label task loss."""

    def __init__(self, temperature: float = 4.0, alpha: float = 0.7) -> None:
        super().__init__()
        if temperature <= 0.0:
            raise ValueError("Temperature must be strictly greater than 0.0")
        if not (0.0 <= alpha <= 1.0):
            raise ValueError("Alpha must be between 0.0 and 1.0 inclusive")

        self.temperature = temperature
        self.alpha = alpha
        self.kl_div = nn.KLDivLoss(reduction="batchmean")
        self.ce_loss = nn.CrossEntropyLoss()
        self.mse_loss = nn.MSELoss()

    def forward(
        self,
        student_logits: torch.Tensor,
        teacher_logits: torch.Tensor,
        targets: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Compute composite distillation loss.

        Returns: (total_loss, distillation_loss, task_loss)
        """
        # Validate logit dimension compatibility
        if student_logits.shape != teacher_logits.shape:
            raise ValueError(
                f"Incompatible logit dimensions: student {student_logits.shape} vs teacher {teacher_logits.shape}."
            )

        T = self.temperature

        # 1. Soft-targets Distillation Loss with Temperature Scaling
        # teacher_soft = softmax(teacher_logits / T)
        teacher_soft = F.softmax(teacher_logits / T, dim=-1)
        # student_log_soft = log_softmax(student_logits / T)
        student_log_soft = F.log_softmax(student_logits / T, dim=-1)

        # Scale KL divergence by T^2 to preserve gradient magnitude
        distill_loss = self.kl_div(student_log_soft, teacher_soft) * (T ** 2)

        # 2. Hard-labels Task Loss (if targets are provided)
        if targets is not None and self.alpha < 1.0:
            if targets.dtype in (torch.long, torch.int, torch.int64):
                task_loss = self.ce_loss(student_logits, targets)
            else:
                task_loss = self.mse_loss(student_logits, targets)
        else:
            task_loss = torch.tensor(0.0, device=student_logits.device)

        # 3. Composite Loss Calculation
        if targets is None or self.alpha == 1.0:
            total_loss = distill_loss
        elif self.alpha == 0.0:
            total_loss = task_loss
        else:
            total_loss = (self.alpha * distill_loss) + ((1.0 - self.alpha) * task_loss)

        return total_loss, distill_loss, task_loss


__all__ = ["DistillationLoss"]
