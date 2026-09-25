"""Phase 9 RAG Model Adapter.

Provides a clean interface connecting RAGService to PyTorch ModelService,
allowing future PyTorch text/generation/reranker models to augment RAG generation
without replacing the existing Ollama/Gemini/fallback execution paths.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

from ..models.service import ModelService, get_model_service

log = logging.getLogger("gen-transform.rag.model_adapter")


class RAGModelAdapter:
    """Adapter decoupling RAG execution from specific PyTorch model management logic."""

    def __init__(self, model_service: Optional[ModelService] = None) -> None:
        self.model_svc = model_service or get_model_service()

    def generate_with_pytorch_model(
        self,
        model_id: str,
        prompt_dict: Dict[str, str],
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Tuple[str, float]]:
        """Attempt text generation using a registered PyTorch model in ModelService."""
        if not self.model_svc.registry.has(model_id):
            log.debug("PyTorch model '%s' not registered in ModelService, skipping PyTorch generation.", model_id)
            return None

        try:
            input_text = f"{prompt_dict.get('system', '')}\n\n{prompt_dict.get('user', '')}"
            res = self.model_svc.predict(model_id=model_id, inputs=input_text, params=params or {})
            outputs = res.outputs

            if isinstance(outputs, str):
                return outputs, res.latency_ms
            elif isinstance(outputs, list):
                return str(outputs), res.latency_ms
            return str(outputs), res.latency_ms

        except Exception as exc:
            log.warning("PyTorch model RAG generation call failed for '%s': %s", model_id, exc)
            return None


__all__ = ["RAGModelAdapter"]
