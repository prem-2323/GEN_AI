"""text/qwen_service.py — Qwen via local Ollama for image & video prompt pipelines.

Single source of truth for prompt-engineering calls made from
``image/prompt_engine.py`` and ``video/planner.py``.

Contract used by those modules:
    generate_with_qwen(prompt, num_predict=..., timeout=...) -> str
    QwenServiceError
"""

from __future__ import annotations

import logging
import re
from typing import Optional

log = logging.getLogger("gen-transform.text.qwen_service")

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen3:4b"
DEFAULT_NUM_PREDICT = 800
DEFAULT_TIMEOUT = 120.0


class QwenServiceError(Exception):
    """Raised when the local Qwen (Ollama) service is unavailable or fails."""


def _strip_think(raw: str) -> str:
    """Remove Qwen3 ``<think>...</think>`` blocks and code fences."""
    cleaned = re.sub(r"<think>.*?</think>", "", raw or "", flags=re.DOTALL).strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.IGNORECASE).strip()
    return cleaned


def generate_with_qwen(
    prompt: str,
    model: str = DEFAULT_MODEL,
    num_predict: int = DEFAULT_NUM_PREDICT,
    timeout: float = DEFAULT_TIMEOUT,
    temperature: float = 0.3,
) -> str:
    """Send a prompt to local Qwen (Ollama) and return the cleaned text output.

    Raises:
        QwenServiceError: If Ollama is unreachable, times out, or errors.
    """
    try:
        import requests
    except ImportError as exc:  # pragma: no cover - requests ships with backend deps
        raise QwenServiceError("The 'requests' package is not installed.") from exc

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "think": False,  # disable Qwen3 extended thinking for clean output
        "options": {
            "num_predict": int(num_predict),
            "temperature": float(temperature),
        },
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=(5.0, float(timeout)),
        )
        response.raise_for_status()
    except requests.exceptions.Timeout as exc:
        raise QwenServiceError("Ollama timed out while generating text.") from exc
    except requests.exceptions.RequestException as exc:
        raise QwenServiceError(f"Ollama is unavailable: {exc}") from exc

    raw = (response.json().get("response") or "").strip()
    if not raw:
        raise QwenServiceError("Qwen returned an empty response.")
    return _strip_think(raw)


def is_qwen_available(timeout: float = 1.5) -> bool:
    """Cheap probe so callers can degrade gracefully when Ollama is offline."""
    try:
        import requests

        response = requests.get(
            "http://localhost:11434/api/tags", timeout=float(timeout)
        )
        return response.status_code == 200
    except Exception:
        return False
