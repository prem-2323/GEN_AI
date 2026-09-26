"""DocLink model interface — provider-agnostic LLM access for Phase 4.

    DocLink extractors
          |
          v
    DocLinkLLM  (abstract protocol — this module)
          |
          +--> OllamaDocLinkLLM   (local Qwen, private)
          +--> GeminiDocLinkLLM   (remote, when a key exists)
          +--> NullDocLinkLLM     (offline / deterministic-only mode)

Extractors never import ``ollama`` or ``google.genai`` directly. Swapping the
provider (or dropping in the Phase 9 PyTorch model layer) is a one-line change
here or via ``configure_doclink_llm()``.
"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from ..core.config import get_settings

log = logging.getLogger("gen-transform.doclink.model")

_PROBE_TTL_SECONDS = 60.0
_PROBE_CACHE: Dict[str, Any] = {"ts": 0.0, "ok": False, "models": []}
_OVERRIDE: Optional["DocLinkLLM"] = None


def _coerce_json(raw: Any) -> Optional[Dict[str, Any]]:
    """Extract the first JSON object from a model response (tolerates fences/prose)."""
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, re.I)
        candidate = m.group(1).strip() if m else raw.strip()
        if not candidate.startswith("{"):
            s, e = candidate.find("{"), candidate.rfind("}")
            if s != -1 and e != -1 and e > s:
                candidate = candidate[s : e + 1]
        parsed = json.loads(candidate)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


@runtime_checkable
class DocLinkLLM(Protocol):
    """Minimal provider contract required by the DocLink extractors."""

    name: str

    def is_available(self) -> bool:
        """True when the provider can serve a request right now."""
        ...

    def generate_json(self, system: str, prompt: str) -> Optional[Dict[str, Any]]:
        """Return a parsed JSON object, or ``None`` so the caller can fall back."""
        ...


class NullDocLinkLLM:
    """Deterministic-only mode: never calls a model, always signals fallback."""

    name = "deterministic"

    def is_available(self) -> bool:
        return False

    def generate_json(self, system: str, prompt: str) -> Optional[Dict[str, Any]]:
        return None


class OllamaDocLinkLLM:
    """Local Ollama provider (Qwen role) with strict-JSON chat formatting."""

    def __init__(self, model: str = "", host: str = "", timeout: float = 3.0) -> None:
        settings = get_settings()
        self.model = model or settings.text_model
        self.host = host or settings.ollama_base_url
        self.timeout = timeout
        self.name = f"ollama:{self.model}"

    def _client(self):
        try:
            import ollama

            return ollama.Client(host=self.host, timeout=self.timeout)
        except Exception as exc:  # pragma: no cover - optional dependency
            log.debug("ollama client unavailable: %s", exc)
            return None

    def is_available(self) -> bool:
        return get_settings().ollama_enabled and _probe_ollama()[0]

    def generate_json(self, system: str, prompt: str) -> Optional[Dict[str, Any]]:
        client = self._client()
        if client is None:
            return None
        try:
            resp = client.chat(
                model=self.model,
                format="json",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            )
            content = ""
            if isinstance(resp, dict):
                content = (resp.get("message") or {}).get("content", "")
            else:  # pragma: no cover - defensive
                content = getattr(getattr(resp, "message", None), "content", "")
            return _coerce_json(content)
        except Exception as exc:
            log.info("DocLink ollama request failed (%s); falling back", str(exc)[:150])
            return None


class GeminiDocLinkLLM:
    """Gemini provider (used only when an API key is configured)."""

    def __init__(self, model: str = "", api_key: str = "", timeout: float = 45.0) -> None:
        settings = get_settings()
        self.model = model or settings.gemini_model
        self.api_key = api_key or settings.gemini_api_key
        self.timeout = timeout
        self.name = f"gemini:{self.model}"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate_json(self, system: str, prompt: str) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            return None
        try:
            from google import genai

            client = genai.Client(api_key=self.api_key)
            resp = client.models.generate_content(
                model=self.model,
                contents=f"{system}\n\n{prompt}",
                config={"responseMimeType": "application/json"},
            )
            return _coerce_json(getattr(resp, "text", "") or "")
        except Exception as exc:
            log.info("DocLink gemini request failed (%s); falling back", str(exc)[:150])
            return None


def _probe_ollama() -> tuple[bool, List[str]]:
    """Cached availability probe (1.5s timeout, 60s TTL) so requests stay fast."""
    now = time.time()
    if now - float(_PROBE_CACHE.get("ts") or 0.0) < _PROBE_TTL_SECONDS:
        return bool(_PROBE_CACHE.get("ok")), list(_PROBE_CACHE.get("models") or [])
    ok, models = False, []
    if get_settings().ollama_enabled:
        try:
            from ..services.ai.orchestrator import check_ollama_models

            ok, models = check_ollama_models()
        except Exception as exc:  # pragma: no cover - defensive
            log.debug("ollama probe failed: %s", exc)
    _PROBE_CACHE.update({"ts": now, "ok": ok, "models": models})
    return ok, models


def configure_doclink_llm(llm: Optional["DocLinkLLM"]) -> None:
    """Inject a provider instance (tests, custom deployments, Phase 9 PyTorch layer)."""
    global _OVERRIDE
    _OVERRIDE = llm


def reset_doclink_llm() -> None:
    """Clear an injected provider and the cached availability probe."""
    global _OVERRIDE
    _OVERRIDE = None
    _PROBE_CACHE.update({"ts": 0.0, "ok": False, "models": []})


def get_doclink_llm(provider: Optional[str] = None, use_llm: bool = True) -> "DocLinkLLM":
    """Resolve the active DocLink provider chain: Ollama -> Gemini -> deterministic."""
    if _OVERRIDE is not None:
        return _OVERRIDE
    if not use_llm:
        return NullDocLinkLLM()

    requested = (provider or "").strip().lower()
    if requested in ("none", "null", "deterministic", "off"):
        return NullDocLinkLLM()
    if requested.startswith("ollama"):
        candidate: "DocLinkLLM" = OllamaDocLinkLLM()
        return candidate if candidate.is_available() else NullDocLinkLLM()
    if requested.startswith("gemini"):
        candidate = GeminiDocLinkLLM()
        return candidate if candidate.is_available() else NullDocLinkLLM()

    ollama_ok, installed = _probe_ollama()
    settings = get_settings()
    if ollama_ok and any(settings.text_model.lower() in m.lower() for m in installed):
        return OllamaDocLinkLLM()
    log.info("DocLink running in deterministic mode (Ollama offline/model missing)")
    return NullDocLinkLLM()


__all__ = [
    "DocLinkLLM",
    "NullDocLinkLLM",
    "OllamaDocLinkLLM",
    "GeminiDocLinkLLM",
    "configure_doclink_llm",
    "reset_doclink_llm",
    "get_doclink_llm",
]
