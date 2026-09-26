"""Direct Text, Audio, PPTX, Brand Voice & Audience Reframing API routes."""
from __future__ import annotations

import io
import json
import logging
import os
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from ...models.text_schemas import (
    AudioRequest,
    AudioResponse,
    AudienceReframeRequest,
    AudienceReframeResponse,
    BrandVoiceProfile,
    FileTextResponse,
    TextRequest,
    TextResponse,
    VideoAudioRequest,
)
from ...services.ai.qwen_service import generate_qwen_json
from ...services.extraction.extraction_service import extract_content
from ...services.presentation.pptx_generator import create_pptx_presentation, THEME_PALETTES
from ...services.audio.tts_service import (
    RECOMMENDED_VOICES,
    extract_video_script_narration,
    generate_audio,
)

log = logging.getLogger("gen-transform.direct_routes")

router = APIRouter(tags=["direct_text_transformation"])

AUDIO_DIR = Path("storage/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

CURRENT_BRAND_PROFILE = BrandVoiceProfile()

AUDIENCE_PROMPT_MAP = {
    "CEO or executives": (
        "Reframe for C-level Executives & CEOs. "
        "Focus on strategic ROI, business impact, key metrics, zero fluff, and executive decisions."
    ),
    "Technical teams": (
        "Reframe for Technical Teams & Engineers. "
        "Focus on system architecture, API schemas, tech stack, data mechanics, and implementation specifics."
    ),
    "General public": (
        "Reframe for the General Public. "
        "Use plain language, zero technical jargon, relatable analogies, and clear practical benefits."
    ),
    "Students": (
        "Reframe for Students & Academic Learners. "
        "Format as an educational breakdown with foundational principles, key definitions, and step-by-step concepts."
    ),
    "Customers": (
        "Reframe for Customers & Prospective Clients. "
        "Focus on customer value proposition, problem solved, ease of use, product benefits, and clear CTA."
    ),
    "Journalists": (
        "Reframe for Journalists & Media Outlets. "
        "Write in press-release style with a strong news hook, quote-worthy statements, key statistics, and industry significance."
    ),
    "Government officials": (
        "Reframe for Government Officials & Policy Makers. "
        "Focus on regulatory compliance, public policy alignment, risk assessment, governance, and public interest."
    ),
}


class GenerateDeckRequest(BaseModel):
    mode: str = "topic"  # "topic" or "content"
    topic_or_content: str
    num_slides: int = Field(6, ge=3, le=15)
    audience: str = "General public"
    tone: str = "Professional"
    language: str = "English"
    detail_level: str = "Medium"
    objective: str = "Inform"
    theme: str = "spotify_emerald"


class ExportDeckRequest(BaseModel):
    presentation: Dict[str, Any]
    theme: str = "spotify_emerald"
    filename: Optional[str] = "presentation.pptx"


# ---------------------------------------------------------------------------
# Audio Endpoints
# ---------------------------------------------------------------------------

@router.post("/api/generate-audio", response_model=AudioResponse)
@router.post("/generate-audio", response_model=AudioResponse, include_in_schema=False)
async def generate_audio_endpoint(request: AudioRequest):
    """Convert text into an MP3 audio file using neural Edge TTS with local fallback."""
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    filename = f"{uuid.uuid4().hex[:12]}.mp3"
    output_path = AUDIO_DIR / filename
    spoken_text = request.text.strip()

    try:
        await generate_audio(
            text=spoken_text,
            output_file=str(output_path),
            voice=request.voice,
        )
    except Exception as err:
        log.error("Audio generation failed: %s", err)
        raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(err)}")

    return AudioResponse(
        status="success",
        filename=filename,
        audio_path=str(output_path),
        download_url=f"/api/audio/{filename}",
        voice=request.voice,
        spoken_text=spoken_text,
        translated=False,
    )


@router.post("/api/generate-video-audio", response_model=AudioResponse)
@router.post("/generate-video-audio", response_model=AudioResponse, include_in_schema=False)
async def generate_video_audio_endpoint(request: VideoAudioRequest):
    """Extract full video script narration and convert it into a single MP3 audio file."""
    narration_text = extract_video_script_narration(request.video_script)
    if not narration_text or not narration_text.strip():
        raise HTTPException(status_code=400, detail="Video script does not contain playable narration text.")

    filename = f"video_script_{uuid.uuid4().hex[:8]}.mp3"
    output_path = AUDIO_DIR / filename

    try:
        await generate_audio(
            text=narration_text,
            output_file=str(output_path),
            voice=request.voice,
        )
    except Exception as err:
        log.error("Video audio generation failed: %s", err)
        raise HTTPException(status_code=500, detail=f"Video audio generation failed: {str(err)}")

    return AudioResponse(
        status="success",
        filename=filename,
        audio_path=str(output_path),
        download_url=f"/api/audio/{filename}",
        voice=request.voice,
        spoken_text=narration_text,
        translated=False,
    )


@router.get("/api/audio/{filename}")
@router.get("/audio/{filename}", include_in_schema=False)
async def get_audio_file(filename: str):
    """Stream or download generated MP3 audio file."""
    candidate = (AUDIO_DIR / filename).resolve()
    storage_root = AUDIO_DIR.resolve()

    if candidate.parent != storage_root or candidate.suffix.lower() not in (".mp3", ".wav"):
        raise HTTPException(status_code=400, detail="Invalid audio filename.")

    if not candidate.is_file():
        raise HTTPException(status_code=404, detail=f"Audio file '{filename}' not found.")

    file_size = candidate.stat().st_size
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
        "Content-Disposition": f'inline; filename="{candidate.name}"',
        "Access-Control-Allow-Origin": "*",
    }

    return FileResponse(
        path=str(candidate),
        media_type="audio/mpeg",
        filename=candidate.name,
        headers=headers,
    )


# ---------------------------------------------------------------------------
# Brand Voice & Reframing
# ---------------------------------------------------------------------------

@router.get("/api/brand-voice/profile", response_model=BrandVoiceProfile)
@router.get("/brand-voice/profile", response_model=BrandVoiceProfile, include_in_schema=False)
def get_brand_voice_profile():
    """Retrieve the saved organization brand voice communication profile."""
    return CURRENT_BRAND_PROFILE


@router.post("/api/brand-voice/profile", response_model=BrandVoiceProfile)
@router.post("/brand-voice/profile", response_model=BrandVoiceProfile, include_in_schema=False)
def save_brand_voice_profile(profile: BrandVoiceProfile):
    """Save or update the organization brand voice communication profile."""
    global CURRENT_BRAND_PROFILE
    CURRENT_BRAND_PROFILE = profile
    return CURRENT_BRAND_PROFILE


@router.post("/api/audience-reframe", response_model=AudienceReframeResponse)
@router.post("/api/reframing", response_model=AudienceReframeResponse)
@router.post("/audience-reframe", response_model=AudienceReframeResponse, include_in_schema=False)
@router.post("/reframing", response_model=AudienceReframeResponse, include_in_schema=False)
async def audience_reframe_endpoint(request: AudienceReframeRequest):
    """Generate audience-specific versions tailored to CEOs, engineers, public, journalists, etc."""
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Source text cannot be empty.")

    target_audiences = request.audiences or list(AUDIENCE_PROMPT_MAP.keys())
    bv = request.brand_voice or CURRENT_BRAND_PROFILE
    source_clean = request.text.strip()
    results: Dict[str, str] = {}

    for aud in target_audiences:
        instruction = AUDIENCE_PROMPT_MAP.get(
            aud, f"Reframe content specifically tailored to the knowledge level and informational needs of {aud}."
        )

        prompt = f"""You are an expert audience reframing AI.
SOURCE CONTENT:
{source_clean[:6000]}

TARGET AUDIENCE: {aud}
REFRAMING INSTRUCTION: {instruction}

BRAND VOICE:
- Tone: {bv.brand_tone}
- Preferred Vocab: {', '.join(bv.preferred_vocabulary)}
- Formatting: {bv.formatting_style}

Return a JSON object: {{ "reframed_content": "Clean, highly tailored reframed version for {aud}." }}"""

        try:
            res = generate_qwen_json(prompt, schema={"reframed_content": "string"})
            content = res.get("reframed_content") or ""
            if len(content.strip()) < 30:
                content = f"**{aud.upper()} BRIEF**\n\n{instruction}\n\nKey source takeaway: {source_clean[:300]}"
            results[aud] = content
        except Exception:
            results[aud] = f"**{aud.upper()} BRIEF**\n\n{instruction}\n\nKey source takeaway: {source_clean[:300]}"

    return AudienceReframeResponse(
        status="success",
        source_text_length=len(source_clean),
        reframed_outputs=results,
    )


# ---------------------------------------------------------------------------
# Presentation & PPTX Export
# ---------------------------------------------------------------------------

@router.get("/api/presentation/themes")
@router.get("/presentation/themes", include_in_schema=False)
def list_presentation_themes():
    """List available PPTX theme palettes with hex colors for frontend preview."""
    themes = []
    for name, palette in THEME_PALETTES.items():
        themes.append({
            "id": name,
            "label": name.replace("_", " ").title(),
            "colors": {
                key: "#%02x%02x%02x" % tuple(palette[key])
                for key in ("dark_bg", "accent", "text_body", "box_bg", "card_border", "header")
                if key in palette
            },
            "is_dark_theme": bool(palette.get("is_dark_theme", False)),
        })
    return {"themes": themes}


@router.post("/api/presentation/generate-deck")
@router.post("/presentation/generate-deck", include_in_schema=False)
def generate_presentation_deck(request: GenerateDeckRequest):
    """Generate structured JSON slide deck from a topic or document content."""
    text_input = request.topic_or_content.strip()
    if not text_input:
        raise HTTPException(status_code=400, detail="Topic or content cannot be empty.")

    prompt = f"""You are a World-Class Presentation Designer AI.
Create a structured {request.num_slides}-slide presentation deck on:
"{text_input[:5000]}"

Target Audience: {request.audience}
Tone: {request.tone}
Language: {request.language}

Return STRICT JSON matching this schema:
{{
  "presentation_title": "Executive Presentation Title",
  "subtitle": "Clear Subtitle",
  "theme": "{request.theme}",
  "slides": [
    {{
      "slide_number": 1,
      "title": "Title Slide",
      "layout": "title",
      "subtitle": "Subtitle text",
      "content": [],
      "speaker_notes": "Opening remarks.",
      "visual_recommendation": "Visual layout concept"
    }},
    {{
      "slide_number": 2,
      "title": "Key Executive Takeaways",
      "layout": "bullet_points",
      "content": ["Key point 1", "Key point 2", "Key point 3"],
      "speaker_notes": "Narration for slide 2.",
      "visual_recommendation": "Bar chart or flowchart"
    }},
    {{
      "slide_number": 3,
      "title": "Comparative Analysis",
      "layout": "two_column",
      "column_left": ["Pillar A item 1", "Pillar A item 2"],
      "column_right": ["Pillar B item 1", "Pillar B item 2"],
      "speaker_notes": "Narration for slide 3.",
      "visual_recommendation": "Two-column grid"
    }}
  ]
}}"""

    try:
        data = generate_qwen_json(prompt)
        if not data.get("slides"):
            data = _build_deck_fallback(text_input, request)
        return data
    except Exception:
        return _build_deck_fallback(text_input, request)


def _build_deck_fallback(text: str, req: GenerateDeckRequest) -> dict:
    title = text[:50].rstrip(". ")
    return {
        "presentation_title": title or "Executive Briefing",
        "subtitle": f"Prepared for {req.audience} • {req.tone}",
        "theme": req.theme,
        "slides": [
            {
                "slide_number": 1,
                "title": title or "Executive Briefing",
                "layout": "title",
                "subtitle": f"Prepared for {req.audience}",
                "content": [],
                "speaker_notes": "Welcome to the presentation.",
                "visual_recommendation": "Cover slide with brand bar",
            },
            {
                "slide_number": 2,
                "title": "Executive Overview & Findings",
                "layout": "bullet_points",
                "content": [text[:120], text[120:240] if len(text) > 120 else "Key strategic priority"],
                "speaker_notes": "Core overview of source facts.",
                "visual_recommendation": "Bullet layout with accent badges",
            },
            {
                "slide_number": 3,
                "title": "Action Roadmap & Outcomes",
                "layout": "two_column",
                "column_left": ["Phase 1: Ingestion & Verification", "Phase 2: Deployment"],
                "column_right": ["Outcome: Zero Hallucinations", "Outcome: Enterprise Agility"],
                "speaker_notes": "Summary of next steps.",
                "visual_recommendation": "Two-column comparison card",
            },
        ],
    }


@router.post("/api/presentation/export-pptx")
@router.post("/presentation/export-pptx", include_in_schema=False)
def export_presentation_pptx(request: ExportDeckRequest):
    """Export structured presentation JSON into a downloadable .pptx file."""
    presentation_data = request.presentation
    if not presentation_data:
        raise HTTPException(status_code=400, detail="Presentation data cannot be empty.")

    theme = request.theme or presentation_data.get("theme", "spotify_emerald")
    filename = request.filename or "presentation.pptx"
    if not filename.endswith(".pptx"):
        filename += ".pptx"

    try:
        stream = create_pptx_presentation(presentation_data, theme_name=theme)
        return Response(
            content=stream.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        log.error("PPTX generation failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to generate PowerPoint file: {str(exc)}")
