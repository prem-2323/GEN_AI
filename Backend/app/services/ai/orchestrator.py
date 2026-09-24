"""AI Orchestrator & Analysis Router — coordinates Qwen text, Gemma vision, and Deterministic Grounded Engine."""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import urllib.request
import json

from ...config.settings import get_settings
from ...models.analysis import AnalysisRecord, TextAnalysis, VisualEvidence
from .qwen_service import analyze_text_with_qwen
from .gemma_service import analyze_images_batch

log = logging.getLogger("gen-transform.orchestrator")


def compute_content_hash(text: str) -> str:
    """Compute SHA-256 hash of extracted source text for analysis deduplication."""
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def check_ollama_models() -> Tuple[bool, List[str]]:
    """Query local Ollama instance at /api/tags to detect installed models."""
    settings = get_settings()
    if not settings.ollama_enabled:
        return False, []
    
    url = f"{settings.ollama_base_url.rstrip('/')}/api/tags"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GenTransformAI/1.0"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", [])]
                return True, models
    except Exception:
        pass
    return False, []


def orchestrate_source_analysis(
    project_id: str,
    source_id: str,
    firebase_uid: str,
    extracted_text: str,
    extracted_images: Optional[List[Dict[str, Any]]] = None,
) -> AnalysisRecord:
    """Run Phase 3 understanding: routes through Local LLM, Hybrid, or Deterministic Grounded Engine."""
    settings = get_settings()
    now = datetime.now(timezone.utc).isoformat()
    c_hash = compute_content_hash(extracted_text)
    analysis_id = f"ANA_{source_id}_{c_hash[:8]}"

    # 1. Inspect Ollama status & installed models
    ollama_ok, installed_models = check_ollama_models()
    has_text_model = any(settings.text_model.lower() in m.lower() for m in installed_models)
    has_vision_model = any(settings.vision_model.lower() in m.lower() for m in installed_models)

    if ollama_ok and has_text_model and (has_vision_model or not extracted_images):
        mode = "local_llm"
    elif ollama_ok and has_text_model:
        mode = "hybrid"
    else:
        mode = "deterministic"

    log.info(
        "Analysis Router decided mode '%s' (Ollama: %s, Text Model '%s': %s, Vision Model '%s': %s)",
        mode,
        "ONLINE" if ollama_ok else "OFFLINE",
        settings.text_model,
        has_text_model,
        settings.vision_model,
        has_vision_model,
    )

    # 2. Text Analysis (Qwen / Deterministic Grounded Engine)
    log.info("Starting text analysis for source %s (%d chars)", source_id, len(extracted_text))
    text_analysis, text_source = analyze_text_with_qwen(extracted_text, preferred_model=settings.text_model)

    # 3. Vision Analysis (Gemma / Visual metadata parser)
    visual_evidence: List[VisualEvidence] = []
    if extracted_images:
        log.info("Starting vision analysis for %d extracted image(s)", len(extracted_images))
        visual_evidence = analyze_images_batch(extracted_images)

    # 4. Multimodal Merger
    if visual_evidence:
        for v in visual_evidence:
            if v.metrics:
                for m in v.metrics:
                    text_analysis.metrics.append(
                        text_analysis.metrics[0].__class__(
                            id=f"metric_vis_{len(text_analysis.metrics)+1:03d}",
                            name=str(m.get("name", "Visual Chart Metric")),
                            value=m.get("value", 0),
                            unit=str(m.get("unit", "")),
                            context=f"Visual evidence from {v.type}: {v.description}",
                            confidence=v.confidence,
                            source=v.source,
                        )
                    )

    record = AnalysisRecord(
        id=analysis_id,
        analysisId=analysis_id,
        projectId=project_id,
        sourceId=source_id,
        firebaseUid=firebase_uid,
        contentHash=c_hash,
        textAnalysis=text_analysis,
        visualAnalysis=visual_evidence,
        modelInfo={
            "textModel": settings.text_model if text_source == "ollama" else "deterministic_extractor",
            "visionModel": settings.vision_model if (ollama_ok and has_vision_model) else "deterministic_visual",
        },
        analysisMode=mode,
        status="completed",
        stage="completed",
        progress=100,
        createdAt=now,
        updatedAt=now,
    )

    log.info(
        "Analysis complete for source %s: mode=%s, %d facts, %d entities, %d metrics, %d visual items",
        source_id,
        mode,
        len(text_analysis.facts),
        len(text_analysis.entities),
        len(text_analysis.metrics),
        len(visual_evidence),
    )

    return record
