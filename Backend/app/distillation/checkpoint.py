"""Phase 10 Knowledge Distillation — Checkpointing.

Handles versioned saving and loading of student PyTorch model checkpoints, optimizer state,
distillation metadata, and metrics snapshots.
"""
from __future__ import annotations

import os
import logging
from typing import Any, Dict, Optional, Tuple
import torch

from ..models.base import BasePyTorchModel
from .config import DistillationConfig

log = logging.getLogger("gen-transform.distillation.checkpoint")


class DistillationCheckpointManager:
    """Saves and restores student PyTorch checkpoints and training state."""

    @staticmethod
    def save_checkpoint(
        student_model: BasePyTorchModel,
        optimizer: torch.optim.Optimizer,
        config: DistillationConfig,
        epoch: int,
        metrics: Dict[str, Any],
        checkpoint_path: Optional[str] = None,
    ) -> str:
        """Save versioned student model checkpoint to disk."""
        target_dir = config.checkpoint_dir
        os.makedirs(target_dir, exist_ok=True)

        if not checkpoint_path:
            filename = f"distilled_{student_model.model_id}_epoch{epoch}.pt"
            checkpoint_path = os.path.join(target_dir, filename)

        checkpoint_data = {
            "model_id": student_model.model_id,
            "model_type": student_model.model_type,
            "epoch": epoch,
            "state_dict": student_model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict() if optimizer else None,
            "config": config.model_dump(),
            "metrics": metrics,
        }

        torch.save(checkpoint_data, checkpoint_path)
        log.info("Saved student distillation checkpoint to '%s'", checkpoint_path)
        return checkpoint_path

    @staticmethod
    def load_checkpoint(
        student_model: BasePyTorchModel,
        checkpoint_path: str,
        optimizer: Optional[torch.optim.Optimizer] = None,
    ) -> Dict[str, Any]:
        """Load student model state_dict and return checkpoint metadata dict."""
        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(f"Checkpoint file '{checkpoint_path}' does not exist.")

        data = torch.load(checkpoint_path, map_location=student_model.target_device)
        state_dict = data.get("state_dict", data)
        student_model.load_state_dict(state_dict)
        student_model.eval()

        if optimizer and "optimizer_state_dict" in data and data["optimizer_state_dict"]:
            optimizer.load_state_dict(data["optimizer_state_dict"])

        log.info("Loaded student checkpoint from '%s' (epoch=%s)", checkpoint_path, data.get("epoch"))
        return data


__all__ = ["DistillationCheckpointManager"]
