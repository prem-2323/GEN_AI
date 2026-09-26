"""
video/schemas.py
~~~~~~~~~~~~~~~~
Pydantic request / response models for the video generation and intelligent video planning pipeline.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ── Intelligent Video Planning Models ───────────────────────────────────────────

class PlannedScene(BaseModel):
    scene_number: int = Field(..., description="1-based scene sequence number")
    duration: float = Field(..., description="Calculated duration in seconds (e.g. 5.0s)")
    visual_importance: float = Field(default=0.8, ge=0.0, le=1.0, description="Visual importance score (0.0 to 1.0)")
    visual_tier: str = Field(default="MEDIUM", description="Importance category: HIGH, MEDIUM, LOW")
    narration: str = Field(..., description="Target voiceover narration text")
    estimated_narration_duration: float = Field(..., description="Estimated speech duration in seconds")
    max_word_count: int = Field(..., description="Maximum allowed word count to prevent audio rush")
    visual_prompt: str = Field(..., description="Cinematic diffusion prompt for visual image generation")
    on_screen_text: str = Field(..., description="Punchy headline or stat banner")
    start_time: float = Field(..., description="Start timestamp in video timeline (seconds)")
    end_time: float = Field(..., description="End timestamp in video timeline (seconds)")
    transition_type: str = Field(default="crossfade", description="Transition effect: crossfade, fade, wipe, cut")
    transition_duration: float = Field(default=0.5, description="Transition duration in seconds")
    subtitle_start: str = Field(..., description="SRT formatted start timestamp (HH:MM:SS,mmm)")
    subtitle_end: str = Field(..., description="SRT formatted end timestamp (HH:MM:SS,mmm)")
    source_facts: List[str] = Field(default_factory=list, description="Associated atomic fact IDs (e.g. F001)")


class IntelligentVideoPlan(BaseModel):
    title: str = Field(default="AI Generated Video", description="Video title")
    target_duration: float = Field(..., description="Target total duration in seconds (e.g. 30.0s)")
    total_calculated_duration: float = Field(..., description="Sum of all calculated scene durations")
    num_scenes: int = Field(..., description="Optimal number of scenes determined by planner")
    average_scene_duration: float = Field(..., description="Average seconds per scene")
    pacing: str = Field(default="balanced", description="Pacing profile: fast, balanced, cinematic")
    scenes: List[PlannedScene] = Field(default_factory=list, description="List of planned scenes")
    timeline: List[Dict[str, Any]] = Field(default_factory=list, description="Chronological timeline events")
    ffmpeg_sync_metadata: Dict[str, Any] = Field(default_factory=dict, description="FFmpeg synchronization instructions")


class VideoPlanRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Source content or facts to plan video from")
    target_duration: int = Field(30, ge=10, le=180, description="Target video duration in seconds (e.g. 30s)")
    pacing: str = Field("balanced", description="Video pacing: fast (3-4s/scene), balanced (5s/scene), cinematic (6-8s/scene)")
    language: str = Field("English", description="Narration language")
    tone: str = Field("Professional", description="Narration tone")
    audience: str = Field("General public", description="Target audience")


# ── Video Generation Request ───────────────────────────────────────────────────

class VideoRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=20,
        max_length=8000,
        description="Source content to convert into a video.",
        examples=["Artificial intelligence is transforming modern cities..."],
    )
    target_duration: int = Field(
        30,
        ge=10,
        le=180,
        description="Target duration in seconds (default: 30s -> 6 scenes of 5s each)."
    )
    pacing: str = Field(
        "balanced",
        description="Video pacing: fast, balanced, cinematic."
    )
    language: str = Field(
        "English",
        description="Narration language (passed as context to Qwen and TTS).",
    )
    tone: str = Field(
        "Professional",
        description="Tone of the narration (e.g. Professional, Casual, Educational).",
    )
    audience: str = Field(
        "General public",
        description="Target audience (used to tailor Qwen's scene writing).",
    )
    voice: str = Field(
        "en-US-AriaNeural",
        description="Edge TTS voice for narration.",
    )
    width: int = Field(512, ge=256, le=1024, description="Scene image width in pixels.")
    height: int = Field(512, ge=256, le=1024, description="Scene image height in pixels.")
    steps: int = Field(20, ge=1, le=40, description="Stable Diffusion sampling steps.")


# ── Response ───────────────────────────────────────────────────────────────────

class SceneSummary(BaseModel):
    scene_number: int
    duration: float
    visual_importance: Optional[float] = 0.8
    visual_tier: Optional[str] = "MEDIUM"
    narration: str
    visual_prompt: str
    on_screen_text: str
    start_time: Optional[float] = 0.0
    end_time: Optional[float] = 5.0
    transition_type: Optional[str] = "crossfade"
    subtitle_start: Optional[str] = None
    subtitle_end: Optional[str] = None
    image_file: str
    audio_file: str


class VideoResponse(BaseModel):
    status: str = "success"
    message: str = "Video generated successfully"
    video_file: str = Field(description="Path to the final subtitled MP4.")
    subtitle_file: str = Field(description="Path to the .srt subtitle file.")
    scenes: int = Field(description="Total number of scenes generated.")
    duration: float = Field(description="Total video duration in seconds.")
    video_plan: Optional[IntelligentVideoPlan] = Field(default=None, description="Intelligent video plan metadata")
    scene_details: Optional[List[SceneSummary]] = None
