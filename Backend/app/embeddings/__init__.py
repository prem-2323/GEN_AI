"""
Phase 4+6 Embeddings Module Export
"""

from app.embeddings.config import EmbeddingConfig, get_embedding_config
from app.embeddings.models import (
    SemanticChunk,
    ChunkMetadata,
    VectorRecord,
    SearchResult,
    SearchRequest,
    IndexDocumentResponse,
    IndexingMetrics,
    EmbeddingProvider,
)
from app.embeddings.chunker import SemanticChunker
from app.embeddings.embedder import (
    EmbeddingModelInterface,
    SentenceTransformerEmbeddingModel,
    DeterministicEmbeddingModel,
    OllamaEmbeddingModel,
    GeminiEmbeddingModel,
    get_embedder,
    set_default_embedder,
    clear_embedding_cache,
)
from app.embeddings.interface import VectorStoreInterface
from app.embeddings.vector_store import MemoryVectorStore
from app.embeddings.faiss_store import FAISSVectorStore
from app.embeddings.repository import (
    VectorStoreRepository,
    get_vector_store,
    set_vector_store,
    reset_vector_store,
)
from app.embeddings.service import EmbeddingPipelineService, get_embedding_service

__all__ = [
    "EmbeddingConfig",
    "get_embedding_config",
    "SemanticChunk",
    "ChunkMetadata",
    "VectorRecord",
    "SearchResult",
    "SearchRequest",
    "IndexDocumentResponse",
    "IndexingMetrics",
    "EmbeddingProvider",
    "SemanticChunker",
    "EmbeddingModelInterface",
    "SentenceTransformerEmbeddingModel",
    "DeterministicEmbeddingModel",
    "OllamaEmbeddingModel",
    "GeminiEmbeddingModel",
    "get_embedder",
    "set_default_embedder",
    "clear_embedding_cache",
    "VectorStoreInterface",
    "MemoryVectorStore",
    "FAISSVectorStore",
    "VectorStoreRepository",
    "get_vector_store",
    "set_vector_store",
    "reset_vector_store",
    "EmbeddingPipelineService",
    "get_embedding_service",
]
