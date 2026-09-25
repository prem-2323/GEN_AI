"""Phase 10 Knowledge Distillation — Evaluator.

Audits Teacher and Student PyTorch models on validation data, measuring loss,
accuracy, parameter counts, latency, and returning quantitative comparison metrics.
"""
from __future__ import annotations

import time
import logging
from typing import Tuple
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from ..models.base import BasePyTorchModel
from .schemas import DistillationComparison, DistillationMetrics

log = logging.getLogger("gen-transform.distillation.evaluator")


class KnowledgeDistillationEvaluator:
    """Evaluates PyTorch models and computes quantitative Teacher vs Student comparisons."""

    def evaluate_model(
        self,
        model: BasePyTorchModel,
        dataloader: DataLoader,
        criterion: Optional[nn.Module] = None,
    ) -> DistillationMetrics:
        """Evaluate a PyTorch model on a DataLoader and collect empirical metrics."""
        model.eval()
        device = model.target_device
        loss_fn = criterion or nn.CrossEntropyLoss()

        total_loss = 0.0
        correct_count = 0
        total_samples = 0
        latency_sum_ms = 0.0

        with torch.inference_mode():
            for batch in dataloader:
                if isinstance(batch, (list, tuple)):
                    inputs = batch[0].to(device)
                    targets = batch[1].to(device) if len(batch) > 1 else None
                else:
                    inputs = batch.to(device)
                    targets = None

                t_batch_start = time.time()
                outputs = model(inputs)
                latency_sum_ms += (time.time() - t_batch_start) * 1000

                batch_len = inputs.size(0)
                total_samples += batch_len

                if targets is not None:
                    loss = loss_fn(outputs, targets)
                    total_loss += loss.item() * batch_len

                    if targets.dtype in (torch.long, torch.int, torch.int64):
                        preds = torch.argmax(outputs, dim=-1)
                        correct_count += (preds == targets).sum().item()

        avg_loss = total_loss / max(1, total_samples) if total_samples > 0 else 0.0
        accuracy = correct_count / max(1, total_samples) if total_samples > 0 else 0.0
        avg_latency = latency_sum_ms / max(1, len(dataloader)) if len(dataloader) > 0 else 0.0

        param_count = model.get_parameter_count()
        size_kb = round((param_count * 4) / 1024.0, 2)  # Assuming float32 (4 bytes per param)

        return DistillationMetrics(
            loss=float(round(avg_loss, 4)),
            accuracy=float(round(accuracy, 4)),
            latency_ms=float(round(avg_latency, 2)),
            parameter_count=param_count,
            model_size_kb=size_kb,
        )

    def compare(
        self,
        teacher: BasePyTorchModel,
        student: BasePyTorchModel,
        dataloader: DataLoader,
    ) -> DistillationComparison:
        """Perform side-by-side empirical evaluation of Teacher vs Student."""
        teacher_metrics = self.evaluate_model(teacher, dataloader)
        student_metrics = self.evaluate_model(student, dataloader)

        # Parameter reduction percentage
        t_params = max(1, teacher_metrics.parameter_count)
        s_params = student_metrics.parameter_count
        param_reduction = round(((t_params - s_params) / t_params) * 100.0, 2)

        # Latency change percentage (negative means faster)
        t_lat = max(0.001, teacher_metrics.latency_ms)
        s_lat = student_metrics.latency_ms
        latency_change = round(((s_lat - t_lat) / t_lat) * 100.0, 2)

        # Accuracy delta
        acc_delta = round(student_metrics.accuracy - teacher_metrics.accuracy, 4)

        log.info(
            "Distillation Evaluation: Teacher params=%d (%.2fms), Student params=%d (%.2fms), Param Reduction=%.2f%%",
            t_params,
            teacher_metrics.latency_ms,
            s_params,
            student_metrics.latency_ms,
            param_reduction,
        )

        return DistillationComparison(
            teacher_metrics=teacher_metrics,
            student_metrics=student_metrics,
            parameter_reduction_percent=param_reduction,
            latency_change_percent=latency_change,
            accuracy_delta=acc_delta,
        )


__all__ = ["KnowledgeDistillationEvaluator"]
