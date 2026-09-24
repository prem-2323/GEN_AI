"""Central configuration using Pydantic Settings.

Secret rule: no real credentials live in code. Everything secret comes
from environment / `.env` (git-ignored). Empty defaults fail loudly.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ContentForge AI"
    environment: str = "development"
    port: int = 8000
    frontend_origin: str = "http://localhost:3000"
    extra_cors_origins: str = ""

    # Firebase / Firestore
    firebase_project_id: str = "gen-lang-client-0421331706"
    firestore_database_id: str = "ai-studio-gentransformai-ccc00148-cf41-4379-89fb-7302425611e2"
    firebase_service_account_path: str = "./serviceAccountKey.json"
    firebase_service_account_json: str = ""

    # MongoDB Atlas — database `contentforge`, one DB for all users.
    # Collections: users, projects, sources, uckr, deliverables, validations, jobs (+ temp)
    mongodb_uri: str = ""
    mongo_uri: str = ""
    mongodb_db_name: str = "contentforge"
    temp_log_interval_minutes: int = 30
    temp_ttl_hours: int = 24

    # File storage (Phase 2 local dirs; Phase 8 Firebase Storage bucket when set)
    storage_root: str = "./storage"
    firebase_storage_bucket: str = ""
    max_upload_mb: int = 25
    allowed_upload_exts: str = "pdf,docx,txt,md,png,jpg,jpeg"

    # AI models (Phase 3) — Router: Ollama Qwen/Gemma, Gemini Fallback, Deterministic Grounded Engine
    ollama_enabled: bool = True
    ollama_base_url: str = "http://localhost:11434"
    text_model: str = "qwen3:4b"
    vision_model: str = "gemma3:4b"
    qwen_model: str = "qwen3:4b"
    gemma_model: str = "gemma3:4b"
    ai_fallback_enabled: bool = True
    deterministic_extraction_enabled: bool = True
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # Dev auth bypass for Postman testing (NEVER enable in production)
    dev_bypass_auth: bool = True

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def mongo_connection_string(self) -> str:
        return self.mongodb_uri or self.mongo_uri

    def allowed_exts(self) -> set[str]:
        return {e.strip().lower().lstrip(".") for e in self.allowed_upload_exts.split(",") if e.strip()}

    def max_upload_bytes(self) -> int:
        return max(1, self.max_upload_mb) * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
