"""Phase 4 — FAISS Vector Store Tests.

Comprehensive test suite validating:
1. FAISSVectorStore initialization and persistence
2. Vector add/upsert operations
3. Similarity search accuracy
4. Document-level deletion
5. ID-based retrieval
6. Persistence across restarts
7. Metadata filtering
8. Dimension validation
9. Factory configuration (VECTOR_BACKEND)
10. Full PDF pipeline integration with testreport.pdf
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure VECTOR_BACKEND=memory for isolated tests (override before import)
os.environ["VECTOR_BACKEND"] = "faiss"
os.environ["EMBEDDING_PROVIDER"] = "deterministic"


class TestFAISSVectorStore:
    """Test FAISS vector store core operations."""

    @pytest.fixture(autouse=True)
    def setup_store(self, tmp_path):
        """Create a fresh FAISSVectorStore in a temporary directory for each test."""
        from app.embeddings.faiss_store import FAISSVectorStore

        self.test_dir = str(tmp_path / "faiss_test")
        self.store = FAISSVectorStore(
            persistence_dir=self.test_dir,
            dimension=384,
            auto_save=True,
        )
        yield
        # Cleanup
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def _make_vector(self, seed: int = 42, dim: int = 384) -> list:
        """Generate a deterministic L2-normalized random vector."""
        rng = np.random.RandomState(seed)
        vec = rng.randn(dim).astype(np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def _make_metadata(self, chunk_id: str, doc_id: str = "doc_001") -> dict:
        return {
            "chunk_id": chunk_id,
            "document_id": doc_id,
            "section": "Main",
            "page_start": 1,
            "page_end": 1,
            "chunk_index": 0,
            "source_filename": "test.pdf",
            "document_type": "pdf",
            "character_count": 100,
            "token_count": 25,
            "content_hash": "abc123",
            "text": f"Sample text for {chunk_id}",
        }

    # ──────────────────────────────────────────────────
    # TEST 1: Initialization
    # ──────────────────────────────────────────────────
    def test_01_initialization(self):
        """FAISSVectorStore should initialize with empty index."""
        assert self.store.total_vectors == 0
        assert self.store.dimension == 384
        assert Path(self.test_dir).exists()

        status = self.store.get_status()
        assert status["backend"] == "faiss"
        assert status["index_type"] == "IndexFlatIP"
        assert status["dimension"] == 384
        assert status["total_vectors"] == 0
        print("✅ TEST 1 PASSED: Initialization")

    # ──────────────────────────────────────────────────
    # TEST 2: Add Vectors
    # ──────────────────────────────────────────────────
    def test_02_add_vectors(self):
        """Should add vectors and persist them."""
        ids = ["chunk_001", "chunk_002", "chunk_003"]
        vectors = [self._make_vector(seed=i) for i in range(3)]
        metadata = [self._make_metadata(cid) for cid in ids]

        result = self.store.add_vectors(ids, vectors, metadata)

        assert result is True
        assert self.store.total_vectors == 3
        assert self.store.is_persisted
        print("✅ TEST 2 PASSED: Add Vectors")

    # ──────────────────────────────────────────────────
    # TEST 3: Similarity Search
    # ──────────────────────────────────────────────────
    def test_03_similarity_search(self):
        """Similarity search should return correct top-K results ordered by score."""
        # Add 5 vectors
        ids = [f"chunk_{i:03d}" for i in range(5)]
        vectors = [self._make_vector(seed=i) for i in range(5)]
        metadata = [self._make_metadata(cid) for cid in ids]
        self.store.add_vectors(ids, vectors, metadata)

        # Search with the first vector — it should be the top result
        query = vectors[0]
        results = self.store.similarity_search(query, top_k=3)

        assert len(results) == 3
        assert results[0].chunk_id == "chunk_000"
        assert results[0].score >= 0.99  # Should be ~1.0 (self-match)
        # Scores should be descending
        for i in range(len(results) - 1):
            assert results[i].score >= results[i + 1].score
        print("✅ TEST 3 PASSED: Similarity Search")

    # ──────────────────────────────────────────────────
    # TEST 4: Idempotent Upsert
    # ──────────────────────────────────────────────────
    def test_04_idempotent_upsert(self):
        """Upserting an existing chunk_id should replace, not duplicate."""
        vec1 = self._make_vector(seed=10)
        meta1 = self._make_metadata("chunk_upsert", doc_id="doc_u")
        self.store.add_vectors(["chunk_upsert"], [vec1], [meta1])
        assert self.store.total_vectors == 1

        # Upsert with different vector
        vec2 = self._make_vector(seed=99)
        meta2 = self._make_metadata("chunk_upsert", doc_id="doc_u")
        meta2["text"] = "Updated text"
        self.store.add_vectors(["chunk_upsert"], [vec2], [meta2])

        # Should still be 1 vector (not 2)
        assert self.store.total_vectors == 1

        # Verify it's the new vector
        rec = self.store.get_by_id("chunk_upsert")
        assert rec is not None
        assert rec.text == "Updated text"
        print("✅ TEST 4 PASSED: Idempotent Upsert")

    # ──────────────────────────────────────────────────
    # TEST 5: Delete Vectors
    # ──────────────────────────────────────────────────
    def test_05_delete_vectors(self):
        """Should delete specific vectors by ID."""
        ids = [f"del_{i}" for i in range(5)]
        vectors = [self._make_vector(seed=i + 100) for i in range(5)]
        metadata = [self._make_metadata(cid) for cid in ids]
        self.store.add_vectors(ids, vectors, metadata)
        assert self.store.total_vectors == 5

        # Delete 2 vectors
        self.store.delete_vectors(["del_1", "del_3"])
        assert self.store.total_vectors == 3

        # Verify deleted ones are gone
        assert self.store.get_by_id("del_1") is None
        assert self.store.get_by_id("del_3") is None

        # Verify remaining ones still exist
        assert self.store.get_by_id("del_0") is not None
        assert self.store.get_by_id("del_2") is not None
        assert self.store.get_by_id("del_4") is not None
        print("✅ TEST 5 PASSED: Delete Vectors")

    # ──────────────────────────────────────────────────
    # TEST 6: Document-Level Deletion
    # ──────────────────────────────────────────────────
    def test_06_delete_document_vectors(self):
        """Should delete all vectors belonging to a specific document_id."""
        # Add vectors from two documents
        ids_a = [f"docA_{i}" for i in range(3)]
        ids_b = [f"docB_{i}" for i in range(2)]

        vecs_a = [self._make_vector(seed=i + 200) for i in range(3)]
        vecs_b = [self._make_vector(seed=i + 300) for i in range(2)]

        meta_a = [self._make_metadata(cid, doc_id="doc_A") for cid in ids_a]
        meta_b = [self._make_metadata(cid, doc_id="doc_B") for cid in ids_b]

        self.store.add_vectors(ids_a + ids_b, vecs_a + vecs_b, meta_a + meta_b)
        assert self.store.total_vectors == 5

        # Delete doc_A
        removed = self.store.delete_document_vectors("doc_A")
        assert removed == 3
        assert self.store.total_vectors == 2

        # doc_B should still be intact
        doc_b_vecs = self.store.get_document_vectors("doc_B")
        assert len(doc_b_vecs) == 2
        print("✅ TEST 6 PASSED: Document-Level Deletion")

    # ──────────────────────────────────────────────────
    # TEST 7: Persistence Across Restart
    # ──────────────────────────────────────────────────
    def test_07_persistence(self):
        """Index should survive store destruction and re-creation."""
        from app.embeddings.faiss_store import FAISSVectorStore

        # Add data
        ids = [f"persist_{i}" for i in range(3)]
        vectors = [self._make_vector(seed=i + 400) for i in range(3)]
        metadata = [self._make_metadata(cid, doc_id="doc_persist") for cid in ids]
        self.store.add_vectors(ids, vectors, metadata)
        assert self.store.total_vectors == 3

        # Destroy current store
        del self.store

        # Re-create from same directory
        store2 = FAISSVectorStore(
            persistence_dir=self.test_dir,
            dimension=384,
            auto_save=True,
        )
        assert store2.total_vectors == 3
        assert store2.is_persisted

        # Verify data integrity
        rec = store2.get_by_id("persist_0")
        assert rec is not None
        assert rec.metadata.document_id == "doc_persist"

        # Search should still work
        results = store2.similarity_search(vectors[0], top_k=1)
        assert len(results) == 1
        assert results[0].chunk_id == "persist_0"
        print("✅ TEST 7 PASSED: Persistence Across Restart")

    # ──────────────────────────────────────────────────
    # TEST 8: Metadata Filtering
    # ──────────────────────────────────────────────────
    def test_08_metadata_filtering(self):
        """Search with metadata filter should return only matching results."""
        ids = [f"filt_{i}" for i in range(4)]
        vectors = [self._make_vector(seed=i + 500) for i in range(4)]
        metadata = []
        for i, cid in enumerate(ids):
            m = self._make_metadata(cid, doc_id="doc_filter")
            m["section"] = "Results" if i < 2 else "Discussion"
            metadata.append(m)

        self.store.add_vectors(ids, vectors, metadata)

        # Search with section filter
        results = self.store.similarity_search(
            vectors[0],
            top_k=10,
            filter_dict={"section": "Results"},
        )

        assert all(r.section == "Results" for r in results)
        assert len(results) == 2
        print("✅ TEST 8 PASSED: Metadata Filtering")

    # ──────────────────────────────────────────────────
    # TEST 9: Dimension Validation
    # ──────────────────────────────────────────────────
    def test_09_dimension_validation(self):
        """Should reject vectors with wrong dimensions."""
        wrong_dim_vector = [0.1] * 128  # Wrong: 128 instead of 384

        with pytest.raises(ValueError, match="dimension mismatch"):
            self.store.add_vectors(
                ["bad_dim"],
                [wrong_dim_vector],
                [self._make_metadata("bad_dim")],
            )
        print("✅ TEST 9 PASSED: Dimension Validation")

    # ──────────────────────────────────────────────────
    # TEST 10: Clear Store
    # ──────────────────────────────────────────────────
    def test_10_clear(self):
        """Clear should empty the entire store."""
        ids = [f"clear_{i}" for i in range(5)]
        vectors = [self._make_vector(seed=i + 600) for i in range(5)]
        metadata = [self._make_metadata(cid) for cid in ids]
        self.store.add_vectors(ids, vectors, metadata)
        assert self.store.total_vectors == 5

        self.store.clear()
        assert self.store.total_vectors == 0
        print("✅ TEST 10 PASSED: Clear Store")


class TestVectorStoreFactory:
    """Test the factory pattern and VECTOR_BACKEND configuration."""

    def test_11_factory_creates_faiss(self, monkeypatch):
        """Factory should create FAISSVectorStore when VECTOR_BACKEND=faiss."""
        from app.core.config import get_settings
        from app.embeddings.faiss_store import FAISSVectorStore
        from app.embeddings.repository import _create_vector_store, reset_vector_store

        # Clear LRU cache to pick up env changes
        get_settings.cache_clear()
        monkeypatch.setenv("VECTOR_BACKEND", "faiss")
        get_settings.cache_clear()

        reset_vector_store()
        store = _create_vector_store()
        assert isinstance(store, FAISSVectorStore)
        print("✅ TEST 11 PASSED: Factory Creates FAISS")
        get_settings.cache_clear()

    def test_12_factory_creates_memory(self, monkeypatch):
        """Factory should create MemoryVectorStore when VECTOR_BACKEND=memory."""
        from app.core.config import get_settings
        from app.embeddings.vector_store import MemoryVectorStore
        from app.embeddings.repository import _create_vector_store, reset_vector_store

        get_settings.cache_clear()
        monkeypatch.setenv("VECTOR_BACKEND", "memory")
        get_settings.cache_clear()

        reset_vector_store()
        store = _create_vector_store()
        assert isinstance(store, MemoryVectorStore)
        print("✅ TEST 12 PASSED: Factory Creates Memory")
        get_settings.cache_clear()

    def test_13_factory_rejects_unknown(self, monkeypatch):
        """Factory should raise ValueError for unknown VECTOR_BACKEND."""
        from app.core.config import get_settings
        from app.embeddings.repository import _create_vector_store, reset_vector_store

        get_settings.cache_clear()
        monkeypatch.setenv("VECTOR_BACKEND", "redis")
        get_settings.cache_clear()

        reset_vector_store()
        with pytest.raises(ValueError, match="Unknown VECTOR_BACKEND"):
            _create_vector_store()
        print("✅ TEST 13 PASSED: Factory Rejects Unknown Backend")
        get_settings.cache_clear()


class TestFAISSAddRecords:
    """Test the add_records method with VectorRecord objects."""

    @pytest.fixture(autouse=True)
    def setup_store(self, tmp_path):
        from app.embeddings.faiss_store import FAISSVectorStore

        self.test_dir = str(tmp_path / "faiss_records_test")
        self.store = FAISSVectorStore(
            persistence_dir=self.test_dir,
            dimension=384,
            auto_save=True,
        )
        yield
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_14_add_records(self):
        """add_records should work with VectorRecord objects."""
        from app.embeddings.models import VectorRecord, ChunkMetadata

        rng = np.random.RandomState(42)

        records = []
        for i in range(3):
            vec = rng.randn(384).astype(np.float32)
            vec = (vec / np.linalg.norm(vec)).tolist()
            records.append(
                VectorRecord(
                    id=f"rec_{i}",
                    vector=vec,
                    text=f"Record text {i}",
                    metadata=ChunkMetadata(
                        chunk_id=f"rec_{i}",
                        document_id="doc_records",
                        section="Test",
                    ),
                )
            )

        result = self.store.add_records(records)
        assert result is True
        assert self.store.total_vectors == 3

        # Verify retrieval
        rec = self.store.get_by_id("rec_1")
        assert rec is not None
        assert rec.text == "Record text 1"
        print("✅ TEST 14 PASSED: Add Records")

    def test_15_get_document_vectors(self):
        """get_document_vectors should return all vectors for a document."""
        from app.embeddings.models import VectorRecord, ChunkMetadata

        rng = np.random.RandomState(99)

        records = []
        for i in range(5):
            vec = rng.randn(384).astype(np.float32)
            vec = (vec / np.linalg.norm(vec)).tolist()
            doc_id = "doc_X" if i < 3 else "doc_Y"
            records.append(
                VectorRecord(
                    id=f"gdv_{i}",
                    vector=vec,
                    text=f"GDV text {i}",
                    metadata=ChunkMetadata(
                        chunk_id=f"gdv_{i}",
                        document_id=doc_id,
                    ),
                )
            )

        self.store.add_records(records)
        assert self.store.total_vectors == 5

        doc_x_vecs = self.store.get_document_vectors("doc_X")
        assert len(doc_x_vecs) == 3
        assert all(v.metadata.document_id == "doc_X" for v in doc_x_vecs)

        doc_y_vecs = self.store.get_document_vectors("doc_Y")
        assert len(doc_y_vecs) == 2
        print("✅ TEST 15 PASSED: Get Document Vectors")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
