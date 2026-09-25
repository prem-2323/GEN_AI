"""Phase 9 PyTorch Model Layer — Device Management.

Provides DeviceManager for detecting CPU and CUDA GPU devices with automatic fallback
to CPU when CUDA is unavailable, supporting HPC, Windows, Linux, and CPU-only environments.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional
import torch

log = logging.getLogger("gen-transform.models.device")


class DeviceManager:
    """Manages PyTorch device selection (CPU/CUDA) with automatic fallback and memory audits."""

    @staticmethod
    def is_cuda_available() -> bool:
        """Return True if CUDA GPU acceleration is available."""
        try:
            return torch.cuda.is_available()
        except Exception:
            return False

    @staticmethod
    def get_device(preferred_device: Optional[str] = "auto") -> torch.device:
        """Resolve target PyTorch device.

        If preferred_device is 'auto', uses CUDA if available, else CPU.
        If preferred_device is 'cuda' or 'cuda:X' but CUDA is unavailable,
        automatically falls back to CPU without crashing.
        """
        pref = (preferred_device or "auto").lower().strip()

        if pref == "auto":
            if torch.cuda.is_available():
                dev_str = "cuda:0"
            else:
                dev_str = "cpu"
        elif pref.startswith("cuda"):
            if torch.cuda.is_available():
                dev_str = pref
            else:
                log.warning("CUDA requested (%s) but CUDA is unavailable; falling back to CPU.", pref)
                dev_str = "cpu"
        else:
            dev_str = "cpu"

        try:
            return torch.device(dev_str)
        except Exception as exc:
            log.warning("Failed to initialize torch.device('%s') (%s); defaulting to CPU.", dev_str, exc)
            return torch.device("cpu")

    @staticmethod
    def get_device_info(device: Optional[torch.device] = None) -> Dict[str, Any]:
        """Return diagnostic device information."""
        target_dev = device or DeviceManager.get_device("auto")
        cuda_avail = torch.cuda.is_available()

        info: Dict[str, Any] = {
            "device_type": target_dev.type,
            "device_string": str(target_dev),
            "cuda_available": cuda_avail,
            "torch_version": torch.__version__,
        }

        if cuda_avail and target_dev.type == "cuda":
            try:
                device_idx = target_dev.index if target_dev.index is not None else 0
                info["gpu_name"] = torch.cuda.get_device_name(device_idx)
                info["gpu_count"] = torch.cuda.device_count()
                info["memory_allocated_mb"] = round(torch.cuda.memory_allocated(device_idx) / (1024 * 1024), 2)
                info["memory_reserved_mb"] = round(torch.cuda.memory_reserved(device_idx) / (1024 * 1024), 2)
            except Exception as exc:
                info["gpu_error"] = str(exc)

        return info


__all__ = ["DeviceManager"]
