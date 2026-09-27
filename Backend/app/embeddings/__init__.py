"""
Phase 4+6 Embeddings Module Export
"""

from .config import EmbeddingConfig, get_embedding_config
from .models import (
    SemanticChunk,
    ChunkMetadata,
    VectorRecord,
    SearchResult,
    SearchRequest,
    IndexDocumentResponse,
    IndexingMetrics,
    EmbeddingProvider,
)
from .chunker import SemanticChunker
from .embedder import (
    EmbeddingModelInterface,
    SentenceTransformerEmbeddingModel,
    DeterministicEmbeddingModel,
    OllamaEmbeddingModel,
    get_embedder,
    set_default_embedder,
    clear_embedding_cache,
)
from .interface import VectorStoreInterface
from .vector_store import MemoryVectorStore
from .faiss_store import FAISSVectorStore
from .repository import (
    VectorStoreRepository,
    get_vector_store,
    set_vector_store,
    reset_vector_store,
)
from .service import EmbeddingPipelineService, get_embedding_service

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
