"""Phase 10 Knowledge Distillation — Data Pipeline.

Provides SyntheticDistillationDataset and DataLoader utilities for deterministic
testing and reproducible model distillation runs.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
import torch
from torch.utils.data import DataLoader, Dataset

log = logging.getLogger("gen-transform.distillation.data")


class SyntheticDistillationDataset(Dataset):
    """Deterministic synthetic dataset for testing knowledge distillation pipelines."""

    def __init__(
        self,
        num_samples: int = 100,
        input_dim: int = 8,
        num_classes: int = 4,
        seed: int = 42,
    ) -> None:
        super().__init__()
        self.num_samples = num_samples
        self.input_dim = input_dim
        self.num_classes = num_classes

        # Generator with fixed seed for reproducibility
        g = torch.Generator().manual_seed(seed)
        self.inputs = torch.randn(num_samples, input_dim, generator=g)
        self.targets = torch.randint(0, num_classes, (num_samples,), generator=g)

    def __len__(self) -> int:
        return self.num_samples

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, Dict[str, Any]]:
        return (
            self.inputs[idx],
            self.targets[idx],
            {"sample_id": f"sample_{idx:04d}"},
        )


def create_distillation_dataloader(
    dataset: Dataset,
    batch_size: int = 16,
    shuffle: bool = True,
) -> DataLoader:
    """Create a standard PyTorch DataLoader for distillation training/eval."""
    return DataLoader(dataset=dataset, batch_size=batch_size, shuffle=shuffle)


__all__ = ["SyntheticDistillationDataset", "create_distillation_dataloader"]
