"""Phase 8 — End-to-End Performance Benchmark & VRAM Measurement Suite.

Measures real latency breakdowns across 5 domain queries on `test sample/testreport.pdf`:
1. Vector FAISS Search Latency
2. Neo4j Graph Search Latency
3. RRF Reciprocal Rank Fusion Latency
4. QUBO Matrix Formulation & Solving Latency
5. Context Builder Latency
6. QLoRA Student Inference Latency
7. Grounding & Numerical Validation Latency
8. Total End-to-End Latency
9. Document Ingestion & Vector Indexing Latency
10. CUDA GPU / VRAM Memory Footprint
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
from app.rag.grounded_rag import GroundedRAGService
from app.services.student_service import get_student_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("benchmark_phase8")

BENCHMARK_QUERIES = [
    "What machine learning algorithms were evaluated?",
    "What sensors were used in the IoT architecture?",
    "What CatBoost performance values were reported?",
    "How was the dataset collected and labeled?",
    "What classification problem was addressed?",
]


def run_benchmark():
    print("=" * 70)
    print("PHASE 8 — SYSTEM HARDENING & END-TO-END PERFORMANCE BENCHMARK")
    print("=" * 70)

    # ── Part 1: System & GPU Hardware Audit ──
    cuda_available = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if cuda_available else "N/A (CPU)"
    pytorch_version = torch.__version__
    cuda_version = torch.version.cuda if cuda_available else "N/A"

    print("\n[GPU & System Environment]")
    print(f"  CUDA Available:     {cuda_available}")
    print(f"  GPU Name:           {gpu_name}")
    print(f"  PyTorch Version:    {pytorch_version}")
    print(f"  CUDA Version:       {cuda_version}")

    if cuda_available:
        torch.cuda.reset_peak_memory_stats()
        vram_allocated_mb = torch.cuda.memory_allocated() / (1024 ** 2)
        vram_reserved_mb = torch.cuda.memory_reserved() / (1024 ** 2)
        print(f"  Initial VRAM Alloc: {vram_allocated_mb:.2f} MB")
        print(f"  Initial VRAM Res:   {vram_reserved_mb:.2f} MB")

    # ── Part 2: Document Ingestion Benchmark ──
    pdf_path = Path(__file__).resolve().parent.parent.parent / "test sample" / "testreport.pdf"
    print(f"\n[Document Ingestion Benchmark: {pdf_path.name}]")

    if pdf_path.exists():
        pdf_bytes = pdf_path.read_bytes()

        # 1. Extraction Time
        t0 = time.time()
        ext_res = extract_pdf_document(pdf_bytes, filename=pdf_path.name, document_id="benchmark_doc")
        extraction_time_s = time.time() - t0

        # 2. Embedding & FAISS Indexing Time
        page_texts = {idx + 1: (p.text if hasattr(p, 'text') else p.get('text', '')) for idx, p in enumerate(ext_res.pages)} if ext_res.pages else None
        emb_svc = get_embedding_service()

        t1 = time.time()
        idx_res = emb_svc.index_text(
            text=ext_res.content,
            document_id="benchmark_doc",
            source_filename=pdf_path.name,
            document_type="pdf",
            page_texts=page_texts,
        )
        ingestion_total_s = time.time() - t1

        print(f"  Extraction Latency:     {extraction_time_s * 1000:.2f} ms")
        print(f"  Embedding Latency:      {idx_res.embedding_time_ms:.2f} ms")
        print(f"  FAISS Indexing Latency: {idx_res.index_time_ms:.2f} ms")
        print(f"  Total Ingestion Time:   {(extraction_time_s + ingestion_total_s):.2f} s ({idx_res.total_chunks} chunks)")
    else:
        print("  ⚠️ testreport.pdf not found for ingestion benchmark")
        extraction_time_s, idx_res = 0.0, None

    # ── Part 3: Query Pipeline Benchmarks ──
    print(f"\n[RAG Query Pipeline Benchmark across {len(BENCHMARK_QUERIES)} queries]")
    rag_service = GroundedRAGService()

    query_metrics = []

    for idx, query in enumerate(BENCHMARK_QUERIES, start=1):
        print(f"\n  Running Query {idx}: '{query}'")

        if cuda_available:
            torch.cuda.reset_peak_memory_stats()

        t_start = time.time()
        res = rag_service.answer_query(
            query=query,
            top_k=5,
            qubo_k=3,
            enable_qubo=True,
            max_new_tokens=128,
        )
        elapsed_total_ms = (time.time() - t_start) * 1000

        breakdown = res["latency_breakdown_ms"]

        vram_peak_mb = (torch.cuda.max_memory_allocated() / (1024 ** 2)) if cuda_available else 0.0

        q_metric = {
            "query_idx": idx,
            "query": query,
            "retrieval_ms": breakdown["retrieval_ms"],
            "faiss_ms": res["retrieval"]["faiss_search_time_ms"],
            "neo4j_ms": res["retrieval"]["neo4j_search_time_ms"],
            "rrf_ms": res["retrieval"]["fusion_time_ms"],
            "qubo_ms": breakdown["qubo_ms"],
            "context_build_ms": breakdown["context_build_ms"],
            "student_generation_ms": breakdown["student_generation_ms"],
            "grounding_validation_ms": breakdown.get("validation_ms", 0.0),
            "total_ms": round(elapsed_total_ms, 2),
            "peak_vram_mb": round(vram_peak_mb, 2),
            "grounding_pass": res["grounding"]["grounding_pass"],
            "numerical_valid": res["grounding"]["numerical_valid"],
            "citations_count": len(res["citations"]),
        }
        query_metrics.append(q_metric)

        print(f"    Vector (FAISS):     {q_metric['faiss_ms']:.2f} ms")
        print(f"    Graph (Neo4j):      {q_metric['neo4j_ms']:.2f} ms")
        print(f"    RRF Fusion:         {q_metric['rrf_ms']:.2f} ms")
        print(f"    QUBO Solver:        {q_metric['qubo_ms']:.2f} ms")
        print(f"    Context Build:      {q_metric['context_build_ms']:.2f} ms")
        print(f"    QLoRA Generation:   {q_metric['student_generation_ms']:.2f} ms")
        print(f"    Grounding Check:    {q_metric['grounding_validation_ms']:.2f} ms")
        print(f"    Total Latency:      {q_metric['total_ms']:.2f} ms")
        print(f"    Peak VRAM Usage:    {vram_peak_mb:.2f} MB")
        print(f"    Grounding Status:   {'PASS' if q_metric['grounding_pass'] else 'REVIEW'}")

    # ── Summary Calculations ──
    avg_total_ms = sum(m["total_ms"] for m in query_metrics) / len(query_metrics)
    avg_retrieval_ms = sum(m["retrieval_ms"] for m in query_metrics) / len(query_metrics)
    avg_qubo_ms = sum(m["qubo_ms"] for m in query_metrics) / len(query_metrics)
    avg_student_ms = sum(m["student_generation_ms"] for m in query_metrics) / len(query_metrics)
    avg_grounding_ms = sum(m["grounding_validation_ms"] for m in query_metrics) / len(query_metrics)
    peak_vram_all = max(m["peak_vram_mb"] for m in query_metrics) if query_metrics else 0.0

    benchmark_results = {
        "hardware": {
            "cuda_available": cuda_available,
            "gpu_name": gpu_name,
            "pytorch_version": pytorch_version,
            "cuda_version": cuda_version,
            "peak_vram_mb": peak_vram_all,
        },
        "ingestion": {
            "document": pdf_path.name,
            "extraction_ms": round(extraction_time_s * 1000, 2) if pdf_path.exists() else 0.0,
            "embedding_ms": idx_res.embedding_time_ms if idx_res else 0.0,
            "faiss_indexing_ms": idx_res.index_time_ms if idx_res else 0.0,
        },
        "averages_ms": {
            "avg_retrieval_ms": round(avg_retrieval_ms, 2),
            "avg_qubo_ms": round(avg_qubo_ms, 2),
            "avg_student_generation_ms": round(avg_student_ms, 2),
            "avg_grounding_validation_ms": round(avg_grounding_ms, 2),
            "avg_total_ms": round(avg_total_ms, 2),
        },
        "query_details": query_metrics,
    }

    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)
    print(f"  Avg End-to-End Latency:      {avg_total_ms:.2f} ms")
    print(f"  Avg Retrieval Latency:        {avg_retrieval_ms:.2f} ms")
    print(f"  Avg QUBO Latency:             {avg_qubo_ms:.2f} ms")
    print(f"  Avg Student Model Latency:    {avg_student_ms:.2f} ms")
    print(f"  Avg Grounding Check Latency:  {avg_grounding_ms:.2f} ms")
    print(f"  Peak VRAM Footprint:          {peak_vram_all:.2f} MB")
    print("=" * 70)

    # Save metrics JSON for markdown report generation
    out_json = Path(__file__).resolve().parent.parent.parent / "outputs" / "benchmark_phase8_data.json"
    out_json.write_text(json.dumps(benchmark_results, indent=2))
    print(f"Saved benchmark raw data to {out_json}")

    return benchmark_results


if __name__ == "__main__":
    run_benchmark()
