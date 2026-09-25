"""
Phase 6 Test Suite: Semantic Chunking + Embeddings + Vector Store + API Routes
"""
import sys
from pathlib import Path

# Add Backend root directory to sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from fastapi.testclient import TestClient
from app.main import app
from app.embeddings.config import EmbeddingConfig
from app.embeddings.chunker import SemanticChunker
from app.embeddings.embedder import DeterministicEmbeddingModel, set_default_embedder
from app.embeddings.vector_store import MemoryVectorStore
from app.embeddings.repository import reset_vector_store
from app.embeddings.service import EmbeddingPipelineService, get_embedding_service


def test_semantic_chunker():
    print("\n--- Testing Semantic Chunker ---")
    config = EmbeddingConfig(chunk_size=150, chunk_overlap=30, min_chunk_size=20)
    chunker = SemanticChunker(config)

    sample_doc = """## Section 1: NVIDIA H200 GPU
The NVIDIA H200 is a high-performance GPU designed specifically for AI workloads.
It features high-bandwidth HBM3e memory and is used for large-scale model inference.

## Section 2: Transformer Architecture
Transformers rely on self-attention mechanisms to process sequential data in parallel.
This design allows models like GPT-4 and Gemini to scale to hundreds of billions of parameters.
"""
    chunks = chunker.chunk_text(sample_doc, document_id="doc_test_1")

    assert len(chunks) >= 2, f"Expected at least 2 chunks, got {len(chunks)}"
    print(f"[OK] Generated {len(chunks)} semantic chunks.")

    for idx, c in enumerate(chunks):
        assert c.chunk_id is not None
        assert c.document_id == "doc_test_1"
        assert c.section != ""
        assert c.token_count > 0
        assert c.content_hash != ""
        print(f"   Chunk {idx+1}: [{c.section}] (tokens ~{c.token_count}) ID={c.chunk_id[:25]}...")

    # Test empty document rejection
    empty_chunks = chunker.chunk_text("   \n  ", document_id="doc_empty")
    assert len(empty_chunks) == 0, "Empty document should produce 0 chunks"
    print("[OK] Empty document correctly produces 0 chunks.")


def test_embedding_model():
    print("\n--- Testing Embedding Model (Deterministic) ---")
    embedder = DeterministicEmbeddingModel(dimension=384)

    t1 = "OpenAI developed GPT language models for artificial intelligence."
    t2 = "OpenAI built GPT transformer models for machine learning applications."
    t3 = "The history of baking sourdough bread in ancient Egypt."

    v1 = embedder.embed_text(t1)
    v2 = embedder.embed_text(t2)
    v3 = embedder.embed_text(t3)

    assert len(v1) == 384, f"Expected 384 dimensions, got {len(v1)}"
    assert len(v2) == 384
    assert len(v3) == 384

    # Cosine similarity using dot product (since vectors are L2-normalized)
    sim_1_2 = sum(a * b for a, b in zip(v1, v2))
    sim_1_3 = sum(a * b for a, b in zip(v1, v3))

    print(f"   Similarity (AI doc 1 vs AI doc 2): {sim_1_2:.4f}")
    print(f"   Similarity (AI doc 1 vs Sourdough doc): {sim_1_3:.4f}")

    assert sim_1_2 > sim_1_3, "Similar texts must have higher similarity than unrelated texts"
    print("[OK] Semantic similarity ordering verified.")

    # Batch embedding test
    batch_vectors = embedder.embed_batch([t1, t2, t3])
    assert len(batch_vectors) == 3
    assert len(batch_vectors[0]) == 384
    print("[OK] Batch embedding generation verified.")


def test_vector_store():
    print("\n--- Testing Vector Store (MemoryVectorStore) ---")
    reset_vector_store()
    store = MemoryVectorStore(persistence_file=None)
    embedder = DeterministicEmbeddingModel(dimension=384)

    t1 = "OpenAI developed GPT models."
    t2 = "NVIDIA manufactures H200 graphics processing units."

    meta1 = {
        "chunk_id": "c1",
        "document_id": "doc_ai",
        "section": "Intro",
        "page_start": 1,
        "text": t1,
    }
    meta2 = {
        "chunk_id": "c2",
        "document_id": "doc_gpu",
        "section": "Hardware",
        "page_start": 2,
        "text": t2,
    }

    ok = store.add_vectors(
        ids=["c1", "c2"],
        vectors=[embedder.embed_text(t1), embedder.embed_text(t2)],
        metadata=[meta1, meta2],
    )
    assert ok is True
    assert len(store.get_document_vectors("doc_ai")) == 1
    assert len(store.get_document_vectors("doc_gpu")) == 1
    print("[OK] Added 2 records to vector store.")

    # Test idempotency (upsert)
    ok_again = store.add_vectors(
        ids=["c1"],
        vectors=[embedder.embed_text(t1)],
        metadata=[meta1],
    )
    assert ok_again is True
    assert len(store.get_document_vectors("doc_ai")) == 1
    print("[OK] Upsert idempotency verified.")

    # Search test
    query_vec = embedder.embed_text("Which company created GPT models?")
    results = store.similarity_search(query_vec, top_k=2)
    assert len(results) == 2
    assert results[0].document_id == "doc_ai", "Top match should be doc_ai"
    print(f"   Top match: '{results[0].text}' (score: {results[0].score:.4f})")

    # Search with metadata filtering
    filtered_results = store.similarity_search(query_vec, top_k=2, filter_dict={"document_id": "doc_gpu"})
    assert len(filtered_results) == 1
    assert filtered_results[0].document_id == "doc_gpu"
    print("[OK] Metadata filtering verified.")

    # Delete test
    deleted = store.delete_document_vectors("doc_ai")
    assert deleted == 1
    assert len(store.get_document_vectors("doc_ai")) == 0
    print("[OK] Document vector deletion verified.")


def test_embedding_pipeline_service():
    print("\n--- Testing Embedding Pipeline Service ---")
    reset_vector_store()
    service = get_embedding_service()
    embedder = DeterministicEmbeddingModel(dimension=384)
    service.embedder = embedder
    set_default_embedder(embedder)

    text_content = """## Phase 6 Overview
Semantic chunking extracts text sections and chunks them efficiently.
Vectors are generated using an embedding model and stored in a Vector Store.

## RAG Foundation
Phase 6 establishes the vector search foundation for Phase 7 Hybrid RAG.
"""
    res = service.index_text(text_content, document_id="doc_service_test")
    assert res.total_chunks > 0
    assert res.embedding_time_ms >= 0
    assert res.index_time_ms >= 0
    print(f"[OK] Indexed {res.total_chunks} chunks in total time ms.")

    # Search query
    search_res, latency_ms = service.search("How does semantic chunking work?", top_k=2)
    assert len(search_res) > 0
    print(f"[OK] Search returned {len(search_res)} chunks.")
    print(f"   Top result score: {search_res[0].score:.4f}")
    print(f"   Search latency: {latency_ms:.2f}ms")

    # Check document status
    status = service.get_document_status("doc_service_test")
    assert status["total_vectors"] == res.total_chunks
    print("[OK] Document indexing status verified.")


def test_api_routes():
    print("\n--- Testing FastAPI Endpoints ---")
    client = TestClient(app)
    headers = {"X-User-Uid": "test_user_123"}

    # 1. Index text via API
    resp = client.post(
        "/api/embeddings/index-text",
        json={
            "document_id": "api_doc_100",
            "text": "## Microservices Architecture\nFastAPI applications can scale horizontally with stateless routing.\nVector databases enable efficient semantic similarity search.",
            "source_filename": "architecture.md",
            "document_type": "markdown",
        },
        headers=headers,
    )
    assert resp.status_code == 200, f"Index text failed: {resp.text}"
    body = resp.json()
    assert body["ok"] is True
    assert body["document_id"] == "api_doc_100"
    assert body["total_chunks"] > 0
    print("[OK] POST /api/embeddings/index-text successful.")

    # 2. Document status via API
    status_resp = client.get("/api/embeddings/document/api_doc_100", headers=headers)
    assert status_resp.status_code == 200
    assert status_resp.json()["total_vectors"] > 0
    print("[OK] GET /api/embeddings/document/{id} successful.")

    # 3. Search via API
    search_resp = client.post(
        "/api/embeddings/search",
        json={"query": "How do vector databases enable search?", "top_k": 3},
        headers=headers,
    )
    assert search_resp.status_code == 200
    s_body = search_resp.json()
    assert s_body["ok"] is True
    assert len(s_body["results"]) > 0
    print(f"[OK] POST /api/embeddings/search returned {len(s_body['results'])} results.")

    # 4. Delete document via API
    del_resp = client.delete("/api/embeddings/document/api_doc_100", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted_count"] > 0
    print("[OK] DELETE /api/embeddings/document/{id} successful.")

    # Confirm status shows 0 chunks
    post_del_status = client.get("/api/embeddings/document/api_doc_100", headers=headers)
    assert post_del_status.json()["total_vectors"] == 0
    print("[OK] Deletion confirmed in document status.")


if __name__ == "__main__":
    print("=== Running Phase 6 Test Suite ===")
    test_semantic_chunker()
    test_embedding_model()
    test_vector_store()
    test_embedding_pipeline_service()
    test_api_routes()
    print("\n[SUCCESS] ALL PHASE 6 TESTS PASSED SUCCESSFULLY!")
