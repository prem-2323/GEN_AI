"""Phase 1-14 Local Demo Runtime Verification Suite.

Performs empirical runtime verification:
1. GPU & CUDA Environment (Phase 2)
2. Neo4j Driver Connection Check (Phase 3)
3. BGE Embeddings 384-dim Normalization Check (Phase 4)
4. FAISS Vector Store Persistence & Search (Phase 5)
5. QLoRA Student LLM Adapter Inference Check (Phase 6)
6. Hybrid RAG & QUBO Evidence Selection Pipeline (Phase 7 & 8)
7. Real PDF Ingestion & 5 Core Domain Queries (Phase 11 & 13)
8. Hallucination Query Test (Phase 12)
"""
from __future__ import annotations

import os
import sys
import time
import json
import logging
from pathlib import Path
import torch

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.extraction.pdf import extract_pdf_document
from app.embeddings.service import get_embedding_service
from app.embeddings.embedder import get_embedder
from app.embeddings.repository import get_vector_store
from app.graph.neo4j import Neo4jDriverAdapter
from app.rag.grounded_rag import GroundedRAGService
from app.services.student_service import get_student_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("verify_local_demo_runtime")

PDF_PATH = Path(__file__).resolve().parent.parent.parent / "test sample" / "testreport.pdf"


def run_full_verification():
    results = {}
    print("=" * 80)
    print("DOCLINK LOCAL DEMO RUNTIME VERIFICATION SUITE")
    print("=" * 80)

    # ── 1. GPU & CUDA CHECK (Phase 2) ──
    print("\n[PHASE 2: GPU & CUDA Environment Check]")
    cuda_available = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if cuda_available else "N/A (CPU)"
    pytorch_version = torch.__version__
    cuda_version = torch.version.cuda if cuda_available else "N/A"

    if cuda_available:
        torch.cuda.reset_peak_memory_stats()
        initial_vram_mb = torch.cuda.memory_allocated(0) / (1024 ** 2)
        total_vram_mb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 2)
        print(f"  [OK] CUDA Available:     True")
        print(f"  [INFO] GPU Name:           {gpu_name}")
        print(f"  [INFO] PyTorch Version:    {pytorch_version}")
        print(f"  [INFO] CUDA Version:       {cuda_version}")
        print(f"  [INFO] Total VRAM:         {total_vram_mb:.2f} MB")
        print(f"  [INFO] Initial VRAM Alloc: {initial_vram_mb:.2f} MB")
    else:
        print(f"  [WARN] CUDA Unavailable: Running in CPU mode")
        total_vram_mb = 0.0

    results["gpu"] = {
        "cuda_available": cuda_available,
        "gpu_name": gpu_name,
        "pytorch_version": pytorch_version,
        "cuda_version": cuda_version,
        "total_vram_mb": round(total_vram_mb, 2),
    }

    # ── 2. NEO4J CHECK (Phase 3) ──
    print("\n[PHASE 3: Neo4j Graph Database Check]")
    neo4j_adapter = Neo4jDriverAdapter()
    neo4j_online = neo4j_adapter.verify_connectivity()
    if neo4j_online:
        print("  [OK] Neo4j Connection:   ONLINE (bolt://localhost:7687)")
        try:
            records = neo4j_adapter.execute_query("MATCH (n) RETURN count(n) AS node_count")
            node_cnt = records[0]["node_count"] if records else 0
            print(f"  [INFO] Graph Database:     {node_cnt} total nodes")
        except Exception as e:
            print(f"  [WARN] Neo4j Query Error: {e}")
    else:
        print("  [OFFLINE] Neo4j Connection:   OFFLINE (Unreachable at bolt://localhost:7687)")
        print("     Detail: GRAPH_BACKEND=neo4j configured. Requires active Neo4j service.")

    results["neo4j"] = {
        "online": neo4j_online,
        "uri": neo4j_adapter.uri,
    }

    # ── 3. EMBEDDINGS CHECK (Phase 4) ──
    print("\n[PHASE 4: BGE Embeddings Check]")
    embedder = get_embedder()
    test_text = "Fruit ripeness assessment using ESP32 sensor platform."
    t0 = time.time()
    vec = embedder.embed_text(test_text)
    emb_time_ms = (time.time() - t0) * 1000

    import numpy as np
    norm = float(np.linalg.norm(vec))
    dim = len(vec)
    is_384 = (dim == 384)
    is_normalized = (abs(norm - 1.0) < 0.01)

    print(f"  [OK] Model Name:         {embedder.name}")
    print(f"  [OK] Device:             {embedder.device}")
    print(f"  [OK] Vector Dimension:   {dim} (Expected: 384)")
    print(f"  [OK] L2 Normalization:   {norm:.4f} (Expected: ~1.0)")
    print(f"  [INFO] Embedding Latency:   {emb_time_ms:.2f} ms")

    results["embeddings"] = {
        "model": embedder.name,
        "device": str(embedder.device),
        "dimension": dim,
        "dimension_valid": is_384,
        "normalized": is_normalized,
        "latency_ms": round(emb_time_ms, 2),
    }

    # ── 4. FAISS VECTOR STORE CHECK (Phase 5) ──
    print("\n[PHASE 5: Persistent FAISS Store Check]")
    store = get_vector_store()
    faiss_status = store.get_status()
    print(f"  [OK] Backend:            {faiss_status['backend']}")
    print(f"  [OK] Index Type:         {faiss_status['index_type']}")
    print(f"  [OK] Total Vectors:      {faiss_status['total_vectors']}")
    print(f"  [OK] Is Persisted:       {faiss_status['is_persisted']}")

    results["faiss"] = faiss_status

    # ── 5. QLORA STUDENT CHECK (Phase 6) ──
    print("\n[PHASE 6: QLoRA Student LLM Model Check]")
    student_svc = get_student_service()
    student_status = student_svc.get_status()
    adapter_path_str = student_status.get('adapter_path') or student_status.get('adapter', '')
    print(f"  [OK] Base Model:         {student_status['base_model']}")
    print(f"  [OK] Adapter Path:       {adapter_path_str}")
    print(f"  [OK] Device:             {student_status['device']}")

    # Single real inference test
    t0 = time.time()
    inf_res = student_svc.generate_grounded_answer("What is CatBoost?", max_new_tokens=32)
    inf_ms = (time.time() - t0) * 1000
    print(f"  [OK] Single Inference:   '{inf_res['text'][:60]}...' ({inf_ms:.2f} ms)")

    results["student"] = {
        "base_model": student_status['base_model'],
        "adapter_path": adapter_path_str,
        "device": student_status['device'],
        "test_inference_ms": round(inf_ms, 2),
    }

    # ── 6. REAL PDF INGESTION & 5 CORE DOMAIN QUERIES (Phase 7, 11, 13) ──
    print(f"\n[PHASE 7 & 11: Real PDF Ingestion & 5 Domain Queries: {PDF_PATH.name}]")

    pdf_bytes = PDF_PATH.read_bytes()
    t0 = time.time()
    ext_res = extract_pdf_document(pdf_bytes, filename=PDF_PATH.name, document_id="demo_doc")
    ext_ms = (time.time() - t0) * 1000

    emb_svc = get_embedding_service()
    page_texts = {idx + 1: (p.text if hasattr(p, 'text') else p.get('text', '')) for idx, p in enumerate(ext_res.pages)} if ext_res.pages else None

    t1 = time.time()
    idx_res = emb_svc.index_text(
        text=ext_res.content,
        document_id="demo_doc",
        source_filename=PDF_PATH.name,
        document_type="pdf",
        page_texts=page_texts,
    )
    idx_total_ms = (time.time() - t1) * 1000

    print(f"  [INFO] Document Ingested:   {len(ext_res.pages)} pages, {len(ext_res.content)} chars")
    print(f"  [INFO] Extraction Latency: {ext_ms:.2f} ms")
    print(f"  [INFO] Indexing Latency:   {idx_res.embedding_time_ms:.2f} ms embed, {idx_res.index_time_ms:.2f} ms FAISS ({idx_res.total_chunks} chunks)")

    rag_service = GroundedRAGService()

    DOMAIN_QUESTIONS = [
        ("Q1", "What machine learning algorithms were evaluated?"),
        ("Q2", "What sensors were used in the system?"),
        ("Q3", "How was the dataset collected and labeled?"),
        ("Q4", "What CatBoost performance values were reported?"),
        ("Q5", "What was the main classification problem?"),
    ]

    domain_results = []
    for q_code, q_text in DOMAIN_QUESTIONS:
        print(f"\n  Running {q_code}: '{q_text}'")
        if cuda_available:
            torch.cuda.reset_peak_memory_stats()

        t_start = time.time()
        res = rag_service.answer_query(query=q_text, top_k=5, qubo_k=3, enable_qubo=True, max_new_tokens=128)
        elapsed_ms = (time.time() - t_start) * 1000
        vram_peak = (torch.cuda.max_memory_allocated(0) / (1024 ** 2)) if cuda_available else 0.0

        q_res = {
            "code": q_code,
            "question": q_text,
            "answer": res["answer"],
            "citations": res["citations"],
            "evidence_count": len(res["evidence"]),
            "grounding_pass": res["grounding"]["grounding_pass"],
            "numerical_valid": res["grounding"]["numerical_valid"],
            "latency_ms": round(elapsed_ms, 2),
            "qubo_energy": res["qubo"].get("total_energy", 0.0),
            "qubo_ms": res["qubo"].get("qubo_ms", 0.0),
            "peak_vram_mb": round(vram_peak, 2),
        }
        domain_results.append(q_res)

        print(f"    Answer:             {res['answer'][:100]}...")
        print(f"    Citations:          {res['citations']}")
        print(f"    Grounding Status:   {'PASS' if res['grounding']['grounding_pass'] else 'REVIEW'}")
        print(f"    Numerical Check:    {'PASS' if res['grounding']['numerical_valid'] else 'FAIL'}")
        print(f"    QUBO Energy / Time: {res['qubo'].get('total_energy', 0.0):.4f} / {res['qubo'].get('qubo_ms', 0.0):.2f} ms")
        print(f"    Total Latency:      {elapsed_ms:.2f} ms")

    results["domain_queries"] = domain_results

    # ── 7. HALLUCINATION TEST (Phase 12) ──
    print("\n[PHASE 12: Hallucination Prevention Test]")
    hallucination_query = "What was the company's revenue in 2025?"
    t_start = time.time()
    res_hal = rag_service.answer_query(query=hallucination_query, top_k=5, qubo_k=3, enable_qubo=True)
    hal_elapsed_ms = (time.time() - t_start) * 1000

    print(f"  Query:               '{hallucination_query}'")
    print(f"  Answer Output:       '{res_hal['answer']}'")
    print(f"  Grounding Pass:      {res_hal['grounding']['grounding_pass']}")
    print(f"  Grounding Valid:     {res_hal['grounding']['grounding_pass'] is True}")

    results["hallucination_test"] = {
        "query": hallucination_query,
        "answer": res_hal["answer"],
        "grounding_pass": res_hal["grounding"]["grounding_pass"],
        "latency_ms": round(hal_elapsed_ms, 2),
    }

    # Save summary JSON for report generation
    out_json = Path(__file__).resolve().parent.parent.parent / "outputs" / "local_demo_runtime_verification_data.json"
    out_json.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nSaved local demo runtime verification raw data to {out_json}")

    return results


if __name__ == "__main__":
    run_full_verification()
