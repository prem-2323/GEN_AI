"""Phase 4 Validation — FAISS Vector Store + PDF Pipeline Integration.

End-to-end validation using testreport.pdf:
1. Extract PDF text
2. Semantic chunking
3. Real embedding generation (BAAI/bge-small-en-v1.5)
4. FAISS vector store indexing
5. Persistence verification
6. Similarity search validation
7. Document deletion + re-index
"""
from __future__ import annotations

import os
import sys
import time
import shutil
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force FAISS backend
os.environ["VECTOR_BACKEND"] = "faiss"
os.environ["EMBEDDING_PROVIDER"] = "sentence_transformers"
os.environ["EMBEDDING_MODEL"] = "BAAI/bge-small-en-v1.5"

PDF_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..", "test sample", "testreport.pdf"
)

PASSED = 0
FAILED = 0
TOTAL = 0


def report(name: str, passed: bool, detail: str = ""):
    global PASSED, FAILED, TOTAL
    TOTAL += 1
    if passed:
        PASSED += 1
        print(f"  ✅ {name}: PASSED{' — ' + detail if detail else ''}")
    else:
        FAILED += 1
        print(f"  ❌ {name}: FAILED{' — ' + detail if detail else ''}")


def main():
    global PASSED, FAILED, TOTAL

    print("=" * 70)
    print("PHASE 4 VALIDATION — FAISS VECTOR STORE + PDF PIPELINE")
    print("=" * 70)

    # ── Step 0: Verify PDF exists ──
    pdf_abs = os.path.abspath(PDF_PATH)
    if not os.path.exists(pdf_abs):
        print(f"\n❌ CANNOT VALIDATE: testreport.pdf not found at {pdf_abs}")
        return
    print(f"\n📄 PDF: {pdf_abs}")
    print(f"   Size: {os.path.getsize(pdf_abs):,} bytes")

    # ── Step 1: Extract PDF ──
    print("\n-- STEP 1: PDF Extraction --")
    t0 = time.time()
    from app.extraction.pdf import extract_pdf_document

    with open(pdf_abs, "rb") as f:
        pdf_bytes = f.read()

    result = extract_pdf_document(
        file_bytes=pdf_bytes,
        filename="testreport.pdf",
        document_id="testreport_phase4",
    )
    extract_time = time.time() - t0

    full_text = result.content
    pages = result.pages
    page_count = len(pages) if pages else 0

    report("PDF Extraction", bool(full_text), f"{len(full_text):,} chars, {page_count} pages, {extract_time:.2f}s")

    # ── Step 2: Semantic Chunking ──
    print("\n── STEP 2: Semantic Chunking ──")
    t0 = time.time()
    from app.embeddings.chunker import SemanticChunker
    from app.embeddings.config import default_embedding_config

    chunker = SemanticChunker(default_embedding_config)
    chunks = chunker.chunk_text(
        text=full_text,
        document_id="testreport_phase4",
    )
    chunk_time = time.time() - t0
    report("Semantic Chunking", len(chunks) > 0, f"{len(chunks)} chunks in {chunk_time:.3f}s")

    # ── Step 3: Embedding Generation ──
    print("\n── STEP 3: Real Embeddings (BAAI/bge-small-en-v1.5) ──")
    t0 = time.time()
    from app.embeddings.embedder import SentenceTransformerEmbeddingModel

    embedder = SentenceTransformerEmbeddingModel()
    print(f"   Model: {embedder.name}")
    print(f"   Device: {embedder.device}")
    print(f"   Dimension: {embedder.dimension}")
    print(f"   CUDA: {embedder.cuda_available}")

    chunk_texts = [c.text for c in chunks]
    vectors = embedder.embed_batch(chunk_texts)
    embed_time = time.time() - t0

    report("Embedding Generation", len(vectors) == len(chunks),
           f"{len(vectors)}/{len(chunks)} vectors, {embed_time:.2f}s ({embed_time/len(chunks)*1000:.1f}ms/chunk)")

    # Verify normalization
    norms = [np.linalg.norm(v) for v in vectors]
    all_normalized = all(abs(n - 1.0) < 0.01 for n in norms)
    report("L2 Normalization", all_normalized, f"min={min(norms):.4f}, max={max(norms):.4f}")

    # ── Step 4: FAISS Indexing ──
    print("\n── STEP 4: FAISS Vector Store Indexing ──")
    test_dir = tempfile.mkdtemp(prefix="phase4_faiss_")
    try:
        from app.embeddings.faiss_store import FAISSVectorStore
        from app.embeddings.metadata import build_chunk_metadata
        from app.embeddings.models import VectorRecord, ChunkMetadata

        t0 = time.time()
        store = FAISSVectorStore(
            persistence_dir=test_dir,
            dimension=embedder.dimension,
            auto_save=True,
        )

        records = []
        for chunk, vec in zip(chunks, vectors):
            meta = build_chunk_metadata(chunk, source_filename="testreport.pdf", document_type="pdf")
            records.append(VectorRecord(
                id=chunk.chunk_id,
                vector=vec,
                text=chunk.text,
                metadata=meta,
            ))

        store.add_records(records)
        index_time = time.time() - t0

        report("FAISS Indexing", store.total_vectors == len(chunks),
               f"{store.total_vectors} vectors indexed in {index_time:.3f}s")

        status = store.get_status()
        print(f"   Backend: {status['backend']}")
        print(f"   Index Type: {status['index_type']}")
        print(f"   Dimension: {status['dimension']}")
        print(f"   Total Vectors: {status['total_vectors']}")
        print(f"   Persisted: {status['is_persisted']}")

        # ── Step 5: Persistence Verification ──
        print("\n── STEP 5: Persistence Verification ──")
        index_file = Path(test_dir) / "faiss.index"
        meta_file = Path(test_dir) / "metadata.json"

        report("Index File Exists", index_file.exists(), f"{index_file.stat().st_size:,} bytes")
        report("Metadata File Exists", meta_file.exists(), f"{meta_file.stat().st_size:,} bytes")

        # Reload from disk
        store2 = FAISSVectorStore(
            persistence_dir=test_dir,
            dimension=embedder.dimension,
            auto_save=True,
        )
        report("Reload From Disk", store2.total_vectors == len(chunks),
               f"{store2.total_vectors} vectors recovered")

        # Verify a random vector survives persistence
        test_id = chunks[0].chunk_id
        rec = store2.get_by_id(test_id)
        report("Record Integrity After Reload", rec is not None and rec.id == test_id)

        # ── Step 6: Similarity Search ──
        print("\n── STEP 6: Similarity Search Validation ──")
        test_queries = [
            "What are the test results?",
            "laboratory analysis report",
            "patient health information",
            "blood glucose levels",
            "medical examination findings",
        ]

        for query in test_queries:
            t0 = time.time()
            q_vec = embedder.embed_text(query)
            results = store2.similarity_search(q_vec, top_k=3)
            search_time = (time.time() - t0) * 1000

            if results:
                report(
                    f"Search: '{query[:40]}'",
                    len(results) > 0,
                    f"{len(results)} results, top_score={results[0].score:.4f}, latency={search_time:.1f}ms"
                )
            else:
                report(f"Search: '{query[:40]}'", False, "No results")

        # ── Step 7: Document Deletion ──
        print("\n── STEP 7: Document Deletion & Re-index ──")
        deleted_count = store2.delete_document_vectors("testreport_phase4")
        report("Document Deletion", deleted_count == len(chunks),
               f"Deleted {deleted_count}/{len(chunks)} vectors")
        report("Store Empty After Deletion", store2.total_vectors == 0,
               f"Remaining: {store2.total_vectors}")

        # Re-index
        store2.add_records(records)
        report("Re-index After Deletion", store2.total_vectors == len(chunks),
               f"{store2.total_vectors} vectors re-indexed")

        # ── Step 8: Filter Search ──
        print("\n── STEP 8: Filtered Search ──")
        q_vec = embedder.embed_text("test results")
        filtered = store2.similarity_search(
            q_vec,
            top_k=5,
            filter_dict={"document_id": "testreport_phase4"},
        )
        report("Filtered by document_id", len(filtered) > 0, f"{len(filtered)} results")

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)

    # ── FINAL REPORT ──
    print("\n" + "=" * 70)
    print(f"PHASE 4 VALIDATION RESULTS: {PASSED}/{TOTAL} PASSED, {FAILED}/{TOTAL} FAILED")
    print("=" * 70)

    if FAILED == 0:
        print("\n🎉 ALL VALIDATIONS PASSED — Phase 4 FAISS Vector Store is PRODUCTION READY")
    else:
        print(f"\n⚠️  {FAILED} validation(s) failed. Review output above.")

    return FAILED == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
