"""Core shared constants across the application."""
from __future__ import annotations

# Application Defaults
DEFAULT_APP_NAME = "ContentForge AI"
DEFAULT_API_VERSION = "1.0.0"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000

# Document & Ingestion Constraints
DEFAULT_MAX_UPLOAD_MB = 25
DEFAULT_MAX_UPLOAD_BYTES = DEFAULT_MAX_UPLOAD_MB * 1024 * 1024
ALLOWED_UPLOAD_EXTENSIONS = {"pdf", "docx", "txt", "md", "png", "jpg", "jpeg"}

MIME_TYPE_MAP = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
    "md": "text/markdown",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "json": "application/json",
    "mp3": "audio/mpeg",
}

# Document Lifecycle Stages
STAGE_UPLOADED = "uploaded"
STAGE_VALIDATING = "validating"
STAGE_EXTRACTING = "extracting"
STAGE_ANALYZING = "analyzing"
STAGE_UCKR_READY = "uckr_ready"
STAGE_TRANSFORMING = "transforming"
STAGE_COMPLETED = "completed"
STAGE_FAILED = "failed"

ALL_STAGES = [
    STAGE_UPLOADED,
    STAGE_VALIDATING,
    STAGE_EXTRACTING,
    STAGE_ANALYZING,
    STAGE_UCKR_READY,
    STAGE_TRANSFORMING,
    STAGE_COMPLETED,
    STAGE_FAILED,
]

# Deliverable Formats & Types
SUPPORTED_DELIVERABLE_TYPES = [
    "executive_summary",
    "advisory",
    "presentation",
    "video",
]

SUPPORTED_EXPORT_FORMATS = [
    "txt",
    "docx",
    "pdf",
    "pptx",
    "mp3",
    "md",
    "json",
]

# AI / Model Defaults
DEFAULT_TEXT_MODEL = "qwen3:4b"
DEFAULT_VISION_MODEL = "gemma3:4b"
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
