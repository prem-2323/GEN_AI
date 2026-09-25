"""Central application configuration using Pydantic Settings.

Secret rule: No real credentials live in code. Everything secret comes
from environment / `.env` (git-ignored).
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Set
from pydantic_settings import BaseSettings, SettingsConfigDict

from .constants import (
    DEFAULT_APP_NAME,
    DEFAULT_PORT,
    DEFAULT_MAX_UPLOAD_MB,
    DEFAULT_TEXT_MODEL,
    DEFAULT_VISION_MODEL,
    DEFAULT_OLLAMA_URL,
    DEFAULT_GEMINI_MODEL,
)


class Settings(BaseSettings):
    app_name: str = DEFAULT_APP_NAME
    environment: str = "development"
    port: int = DEFAULT_PORT
    frontend_origin: str = "http://localhost:3000"
    extra_cors_origins: str = ""

    # Storage Paths & Limits
    storage_root: str = "./storage"
    document_storage_root: str = "./storage/documents"
    data_storage_root: str = "./storage/data"
    max_upload_mb: int = DEFAULT_MAX_UPLOAD_MB
    allowed_upload_exts: str = "pdf,docx,txt,md,png,jpg,jpeg"

    # AI Model Configuration
    ollama_enabled: bool = True
    ollama_base_url: str = DEFAULT_OLLAMA_URL
    text_model: str = DEFAULT_TEXT_MODEL
    vision_model: str = DEFAULT_VISION_MODEL
    qwen_model: str = DEFAULT_TEXT_MODEL
    gemma_model: str = DEFAULT_VISION_MODEL
    ai_fallback_enabled: bool = True
    deterministic_extraction_enabled: bool = True
    gemini_api_key: str = ""
    gemini_model: str = DEFAULT_GEMINI_MODEL

    # Neo4j Graph Database Configuration
    graph_backend: str = "neo4j"  # "neo4j" | "mock"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "password"
    neo4j_database: str = "neo4j"
    neo4j_enabled: bool = True

    # Vector & Embeddings Configuration (Phase 3, 4, 6 & 7)
    vector_backend: str = "faiss"  # "faiss" | "memory"
    vector_dimension: int = 384
    embedding_provider: str = "sentence_transformers"  # "sentence_transformers" | "mock" | "deterministic"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_device: str = "auto"  # "auto" | "cuda" | "cpu"
    embedding_batch_size: int = 16
    embedding_normalize: bool = True

    # Phase 5 Hybrid Retrieval Configuration
    vector_top_k: int = 10
    graph_top_k: int = 10
    hybrid_top_k: int = 5
    rrf_k: int = 60

    # Teacher Model Configuration
    teacher_model: str = "qwen3:4b"
    teacher_timeout_seconds: int = 180
    teacher_max_retries: int = 2
    dataset_source: str = "grounded"  # "grounded" | "teacher"


    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def allowed_exts(self) -> Set[str]:
        return {e.strip().lower().lstrip(".") for e in self.allowed_upload_exts.split(",") if e.strip()}

    def max_upload_bytes(self) -> int:
        return max(1, self.max_upload_mb) * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
