"""Phase 9 PyTorch Model Layer — Inference Engine.

Executes single & batch PyTorch model inference inside torch.inference_mode(),
managing device tensor transfers, batch size limits, and latency metric tracking.
"""
from __future__ import annotations

import time
import logging
from typing import Any, List, Optional
import torch

from .registry import ModelRegistry
from .schemas import ModelInferenceRequest, ModelInferenceResponse

log = logging.getLogger("gen-transform.models.inference")


class InferenceEngine:
    """Executes gradient-free PyTorch model inference with batching and latency metrics."""

    def __init__(self, registry: ModelRegistry) -> None:
        self.registry = registry

    def run_inference(self, req: ModelInferenceRequest) -> ModelInferenceResponse:
        """Run inference for a single or batch input request."""
        t_start = time.time()
        model_id = req.model_id

        model = self.registry.get(model_id)
        if model is None:
            raise KeyError(f"PyTorch model '{model_id}' is not registered in ModelRegistry.")

        if not model.is_loaded:
            model.initialize()

        raw_input = req.inputs
        batch_size = 1
        is_batch = False

        # Detect batch input list vs single sample
        if isinstance(raw_input, list) and len(raw_input) > 0 and isinstance(raw_input[0], list):
            is_batch = True
            batch_size = len(raw_input)

        device_used = str(model.target_device)

        # Execute inside torch.inference_mode()
        with torch.inference_mode():
            if is_batch:
                # Respect configured max batch size
                max_batch = model.config.batch_size
                outputs: List[Any] = []
                for i in range(0, len(raw_input), max_batch):
                    slice_inputs = raw_input[i : i + max_batch]
                    slice_out = model.predict_batch(slice_inputs)
                    outputs.extend(slice_out)
            else:
                outputs = model.predict(raw_input)

        latency_ms = round((time.time() - t_start) * 1000, 2)

        log.debug(
            "PyTorch inference complete for '%s': batch_size=%d, device=%s in %sms",
            model_id,
            batch_size,
            device_used,
            latency_ms,
        )

        return ModelInferenceResponse(
            model_id=model_id,
            outputs=outputs,
            latency_ms=latency_ms,
            batch_size=batch_size,
            device_used=device_used,
        )


__all__ = ["InferenceEngine"]
