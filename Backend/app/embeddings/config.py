"""Phase 6 Embedding & Vector Store Configuration."""
from __future__ import annotations

from pydantic import BaseModel, Field


class EmbeddingConfig(BaseModel):
    """Configurable settings for semantic chunking, embedding generation & vector search."""
    chunk_size: int = 600
    chunk_overlap: int = 100
    min_chunk_size: int = 50
    max_chunk_size: int = 1200
    top_k: int = 5
    batch_size: int = 16
    embedding_model_name: str = "deterministic-384d"
    vector_dimension: int = 384
    cache_embeddings: bool = True

    model_config = {"extra": "allow"}


default_embedding_config = EmbeddingConfig()


def get_embedding_config() -> EmbeddingConfig:
    return default_embedding_config


__all__ = ["EmbeddingConfig", "default_embedding_config", "get_embedding_config"]
