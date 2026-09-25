"""Phase 3 Real Embeddings Test Suite.

Verifies SentenceTransformerEmbeddingModel initialization, model loading, dimension,
single & batch embeddings, L2 normalization, empty input handling, GPU/CPU detection,
semantic similarity relationships, status API endpoint, and no-silent-fallback behavior.
"""
from __future__ import annotations

import math
import pytest
import torch
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.embeddings.embedder import (
    SentenceTransformerEmbeddingModel,
    DeterministicEmbeddingModel,
    get_embedder,
    set_default_embedder,
)
from app.embeddings.service import EmbeddingPipelineService
from app.embeddings.chunker import SemanticChunker
from app.main import app


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a < 1e-9 or norm_b < 1e-9:
        return 0.0
    return dot / (norm_a * norm_b)


def test_1_provider_initialization_and_loading():
    """Verify loading real SentenceTransformer model (BAAI/bge-small-en-v1.5)."""
    model = SentenceTransformerEmbeddingModel(model_name="BAAI/bge-small-en-v1.5")
    assert model.model_name == "BAAI/bge-small-en-v1.5"
    assert model.dimension == 384
    assert "sentence-transformers" in model.name


def test_2_embedding_dimension_and_shape():
    """Verify single embedding returns list of float of correct dimension."""
    model = SentenceTransformerEmbeddingModel(model_name="BAAI/bge-small-en-v1.5")
    vec = model.embed_text("Deep learning for document transformation and semantic processing.")
    assert isinstance(vec, list)
    assert len(vec) == 384
    assert all(isinstance(v, float) for v in vec)


def test_3_l2_normalization():
    """Verify L2 norm of generated vector is ~1.0."""
    model = SentenceTransformerEmbeddingModel(model_name="BAAI/bge-small-en-v1.5", normalize=True)
    vec = model.embed_text("Testing numerical vector normalization.")
    norm = math.sqrt(sum(v * v for v in vec))
    assert pytest.approx(norm, abs=1e-4) == 1.0


def test_4_batch_embedding():
    """Verify batch embedding produces matching list of vectors."""
    model = SentenceTransformerEmbeddingModel(model_name="BAAI/bge-small-en-v1.5")
    texts = [
        "First sentence for batch test.",
        "Second sentence with different content.",
        "Third sentence summarizing results.",
    ]
    batch_vecs = model.embed_batch(texts, batch_size=2)
    assert len(batch_vecs) == 3
    for v in batch_vecs:
        assert len(v) == 384
        norm = math.sqrt(sum(x * x for x in v))
        assert pytest.approx(norm, abs=1e-4) == 1.0


def test_5_empty_input_handling():
    """Verify empty or whitespace strings return zero vectors without crashing."""
    model = SentenceTransformerEmbeddingModel(model_name="BAAI/bge-small-en-v1.5")
    vec_empty = model.embed_text("")
    assert len(vec_empty) == 384
    assert sum(abs(v) for v in vec_empty) == 0.0

    batch_empty = model.embed_batch(["   ", "valid text", ""])
    assert len(batch_empty) == 3
    assert sum(abs(v) for v in batch_empty[0]) == 0.0
    assert math.sqrt(sum(v * v for v in batch_empty[1])) > 0.99
    assert sum(abs(v) for v in batch_empty[2]) == 0.0


def test_6_device_detection():
    """Verify device selection reflects PyTorch capabilities correctly without faking."""
    model = SentenceTransformerEmbeddingModel(device="auto")
    cuda_is_avail = torch.cuda.is_available()
    assert model.cuda_available == cuda_is_avail
    if cuda_is_avail:
        assert model.device == "cuda"
    else:
        assert model.device == "cpu"

    # CPU fallback explicit test
    cpu_model = SentenceTransformerEmbeddingModel(device="cpu")
    assert cpu_model.device == "cpu"


def test_7_semantic_similarity():
    """Verify semantic similarity relationship: Sim(A, B) > Sim(A, C)."""
    model = SentenceTransformerEmbeddingModel(model_name="BAAI/bge-small-en-v1.5")

    text_a = "CatBoost achieved strong classification performance."
    text_b = "The CatBoost machine learning model performed well for classification."
    text_c = "The weather forecast predicts heavy rainfall tomorrow."

    vec_a = model.embed_text(text_a)
    vec_b = model.embed_text(text_b)
    vec_c = model.embed_text(text_c)

    sim_ab = cosine_similarity(vec_a, vec_b)
    sim_ac = cosine_similarity(vec_a, vec_c)

    assert sim_ab > sim_ac, f"Expected Sim(A,B) {sim_ab:.4f} > Sim(A,C) {sim_ac:.4f}"


def test_8_no_silent_fallback_when_invalid_model():
    """Verify that invalid embedding model raises explicit error instead of silent mock fallback."""
    with pytest.raises(RuntimeError) as exc_info:
        get_embedder(provider="sentence_transformers")
        # Forcing invalid model name inside SentenceTransformerEmbeddingModel
        SentenceTransformerEmbeddingModel(model_name="nonexistent_invalid_huggingface_model_1234567")

    assert "Could not load SentenceTransformer" in str(exc_info.value) or "invalid" in str(exc_info.value).lower()


def test_9_embedding_status_endpoint():
    """Verify GET /api/embeddings/status returns accurate provider details."""
    set_default_embedder(SentenceTransformerEmbeddingModel(model_name="BAAI/bge-small-en-v1.5"))
    try:
        client = TestClient(app)
        headers = {"X-User-Uid": "test_user_001"}
        res = client.get("/api/embeddings/status", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["provider"] == "sentence_transformers"
        assert data["model"] == "BAAI/bge-small-en-v1.5"
        assert data["dimension"] == 384
        assert data["status"] == "ready"
        assert "device" in data
    finally:
        set_default_embedder(None)


def test_10_deterministic_chunking_metadata():
    """Verify semantic chunking produces stable chunk_ids and token estimates."""
    chunker = SemanticChunker()
    text = (
        "SECTION 1: Overview and Objectives\n"
        "This is a comprehensive test paragraph specifically designed to test semantic chunking functionality. "
        "It contains sufficient character length to exceed the minimum chunk size threshold.\n\n"
        "SECTION 2: Detailed Specifications\n"
        "Detailed architecture information and operational constraints are documented within this second section. "
        "Running the chunking engine multiple times must produce identical deterministic chunk IDs."
    )
    chunks_1 = chunker.chunk_text(text, document_id="doc_test")
    chunks_2 = chunker.chunk_text(text, document_id="doc_test")

    assert len(chunks_1) > 0
    assert len(chunks_1) == len(chunks_2)
    for c1, c2 in zip(chunks_1, chunks_2):
        assert c1.chunk_id == c2.chunk_id
        assert c1.content_hash == c2.content_hash
        assert c1.token_count > 0
