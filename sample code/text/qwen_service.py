import os
import re

import requests


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "qwen3:4b")
# Default read timeout. Lowered from 180s so the Consistency Engine can fall
# back to deterministic grounded generation instead of hanging the API.
# Override with OLLAMA_TIMEOUT_SECONDS env var when a slower GPU needs more time.
try:
    REQUEST_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "60"))
except ValueError:
    REQUEST_TIMEOUT_SECONDS = 60.0


class QwenServiceError(Exception):
    """Raised when Ollama cannot complete a generation request."""


def _num_predict_for_prompt(prompt: str) -> int:
    """Pick a tight token budget per task so consistency calls return faster (8-15s)."""
    lowered = (prompt or "").lower()
    if "concise (quick read)" in lowered or "concise" in lowered:
        return 180
    if "linkedin" in lowered:
        return 220
    if "executive summary" in lowered or "summary" in lowered:
        return 220
    if "storyboard" in lowered or "video producer" in lowered or "video" in lowered or "planning" in lowered:
        return 1600
    if "presentation" in lowered or "slide deck" in lowered or "powerpoint" in lowered or "pptx" in lowered:
        return 1200
    if "translator" in lowered or "translate fluently" in lowered:
        return 250
    if "knowledge engineering" in lowered or "atomic facts" in lowered:
        return 300
    return 350


def generate_with_qwen(prompt: str, timeout=None, num_predict=None) -> str:
    """Send generation prompt to local Ollama Qwen model.

    Keeps single-arg compatibility (existing tests monkeypatch with
    ``def fake_qwen(prompt)``) while allowing optional overrides:
    ``generate_with_qwen(prompt, timeout=20, num_predict=200)``.
    """
    read_timeout = float(timeout) if timeout else REQUEST_TIMEOUT_SECONDS
    predict_n = int(num_predict) if num_predict else _num_predict_for_prompt(prompt)

    payload = {
        "model": MODEL_NAME,
        "prompt": f"[DO NOT OUTPUT THINKING MONOLOGUE OR <think> TAGS. RESPOND DIRECTLY AND CONCISELY.]\n\n{prompt}",
        "stream": False,
        "think": False,
        "options": {
            "num_predict": predict_n,
            "temperature": 0.3,
            "top_p": 0.9
        }
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=(3.0, read_timeout)
        )
        response.raise_for_status()
    except requests.exceptions.Timeout as error:
        raise QwenServiceError(
            "Ollama took too long to generate the transformation."
        ) from error
    except requests.exceptions.RequestException as error:
        raise QwenServiceError(
            "Ollama could not process the transformation request."
        ) from error

    data = response.json()
    raw_text = data.get("response", "")

    # Strip internal <think> reasoning tags if emitted by thinking models
    cleaned_text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()
    return cleaned_text if cleaned_text else raw_text.strip()

