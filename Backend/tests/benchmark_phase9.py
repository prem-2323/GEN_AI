"""Phase 9 — Automated Evaluation, Benchmarking & Research-Grade Validation Suite.

Executes comparative evaluation between:
  Baseline Pipeline (FAISS + Neo4j -> RRF Fusion -> Student -> Grounding Check)
versus:
  Final Pipeline    (FAISS + Neo4j -> RRF Fusion -> QUBO Optimization -> Student -> Grounding Check)

Saves empirical raw evaluation results to `outputs/phase9_results.json`.
"""
from __future__ import annotations

import os
import sys
import time
import json
import logging
import statistics
from pathlib import Path
import torch

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.rag.grounded_rag import GroundedRAGService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("benchmark_phase9")


def run_phase9_evaluation():
    print("=" * 75)
    print("PHASE 9 — RESEARCH-GRADE SYSTEM EVALUATION & BENCHMARKING")
    print("=" * 75)

    dataset_path = Path(__file__).resolve().parent / "phase9_evaluation_dataset.json"
    if not dataset_path.exists():
        raise FileNotFoundError(f"Evaluation dataset not found at {dataset_path}")

    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    print(f"\n[Evaluation Dataset Loaded]: {len(dataset)} items from {dataset_path.name}")

    # Hardware Environment Audit
    cuda_available = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if cuda_available else "N/A (CPU)"
    pytorch_version = torch.__version__
    cuda_version = torch.version.cuda if cuda_available else "N/A"

    rag_service = GroundedRAGService()

    baseline_results = []
    final_results = []

    # Set fixed random seed for reproducibility where applicable
    if cuda_available:
        torch.manual_seed(42)
        torch.cuda.manual_seed_all(42)

    print("\nExecuting Comparative Pipeline Benchmarks...")

    for idx, item in enumerate(dataset, start=1):
        q_id = item["id"]
        query = item["question"]
        cat = item["category"]
        expected_ev = item.get("expected_evidence", [])

        print(f"\n  [{q_id}] Category: '{cat}' | Query: '{query[:60]}...'")

        # ── 1. BASELINE PIPELINE (enable_qubo=False) ──
        if cuda_available:
            torch.cuda.reset_peak_memory_stats()
        t0_base = time.time()
        res_base = rag_service.answer_query(query=query, top_k=3, qubo_k=3, enable_qubo=False, max_new_tokens=128)
        lat_base_ms = (time.time() - t0_base) * 1000

        # Calculate evidence keyword recall for baseline
        base_ev_text = " ".join([e.get("text", "") for e in res_base["evidence"]]).lower()
        base_hit_count = sum(1 for exp in expected_ev if exp.get("keyword", "").lower() in base_ev_text)
        base_recall = (base_hit_count / len(expected_ev)) if expected_ev else 1.0

        b_item = {
            "id": q_id,
            "category": cat,
            "query": query,
            "latency_ms": round(lat_base_ms, 2),
            "evidence_count": len(res_base["evidence"]),
            "evidence_recall": round(base_recall, 4),
            "grounding_pass": res_base["grounding"]["grounding_pass"],
            "numerical_valid": res_base["grounding"]["numerical_valid"],
            "citations": res_base["citations"],
            "answer": res_base["answer"],
        }
        baseline_results.append(b_item)

        # ── 2. FINAL PIPELINE (enable_qubo=True) ──
        if cuda_available:
            torch.cuda.reset_peak_memory_stats()
        t0_final = time.time()
        res_final = rag_service.answer_query(query=query, top_k=5, qubo_k=3, enable_qubo=True, max_new_tokens=128)
        lat_final_ms = (time.time() - t0_final) * 1000
        vram_peak_mb = (torch.cuda.max_memory_allocated() / (1024 ** 2)) if cuda_available else 0.0

        final_ev_text = " ".join([e.get("text", "") for e in res_final["evidence"]]).lower()
        final_hit_count = sum(1 for exp in expected_ev if exp.get("keyword", "").lower() in final_ev_text)
        final_recall = (final_hit_count / len(expected_ev)) if expected_ev else 1.0

        breakdown = res_final["latency_breakdown_ms"]

        f_item = {
            "id": q_id,
            "category": cat,
            "query": query,
            "latency_breakdown_ms": {
                "embedding_ms": res_final["retrieval"].get("embedding_time_ms", 0.0),
                "faiss_ms": res_final["retrieval"].get("faiss_search_time_ms", 0.0),
                "neo4j_ms": res_final["retrieval"].get("neo4j_search_time_ms", 0.0),
                "rrf_ms": res_final["retrieval"].get("fusion_time_ms", 0.0),
                "qubo_ms": breakdown.get("qubo_ms", 0.0),
                "context_build_ms": breakdown.get("context_build_ms", 0.0),
                "student_generation_ms": breakdown.get("student_generation_ms", 0.0),
                "validation_ms": breakdown.get("validation_ms", 0.0),
                "total_ms": round(lat_final_ms, 2),
            },
            "peak_vram_mb": round(vram_peak_mb, 2),
            "evidence_count": len(res_final["evidence"]),
            "evidence_recall": round(final_recall, 4),
            "qubo_details": {
                "qubo_enabled": res_final["qubo"].get("qubo_enabled", True),
                "solver_type": res_final["qubo"].get("solver_type", "exact"),
                "total_energy": res_final["qubo"].get("total_energy", 0.0),
                "qubo_ms": res_final["qubo"].get("qubo_ms", 0.0),
            },
            "grounding_pass": res_final["grounding"]["grounding_pass"],
            "numerical_valid": res_final["grounding"]["numerical_valid"],
            "citations": res_final["citations"],
            "answer": res_final["answer"],
        }
        final_results.append(f_item)

        print(f"    Baseline Latency: {lat_base_ms:.2f} ms | Grounding: {'PASS' if b_item['grounding_pass'] else 'FAIL'}")
        print(f"    Final    Latency: {lat_final_ms:.2f} ms | Grounding: {'PASS' if f_item['grounding_pass'] else 'FAIL'} | QUBO Energy: {f_item['qubo_details']['total_energy']:.4f}")

    # ── Calculate Summary Statistics ──
    total_q = len(dataset)
    base_pass_count = sum(1 for r in baseline_results if r["grounding_pass"])
    final_pass_count = sum(1 for r in final_results if r["grounding_pass"])

    base_num_pass = sum(1 for r in baseline_results if r["numerical_valid"])
    final_num_pass = sum(1 for r in final_results if r["numerical_valid"])

    base_avg_recall = sum(r["evidence_recall"] for r in baseline_results) / total_q
    final_avg_recall = sum(r["evidence_recall"] for r in final_results) / total_q

    final_tot_latencies = [r["latency_breakdown_ms"]["total_ms"] for r in final_results]
    final_qubo_latencies = [r["latency_breakdown_ms"]["qubo_ms"] for r in final_results]
    final_student_latencies = [r["latency_breakdown_ms"]["student_generation_ms"] for r in final_results]
    final_faiss_latencies = [r["latency_breakdown_ms"]["faiss_ms"] for r in final_results]

    stats = {
        "hardware": {
            "cuda_available": cuda_available,
            "gpu_name": gpu_name,
            "pytorch_version": pytorch_version,
            "cuda_version": cuda_version,
            "peak_vram_mb": max(r["peak_vram_mb"] for r in final_results) if final_results else 0.0,
        },
        "evaluation_summary": {
            "total_questions": total_q,
            "baseline_grounding_pass": f"{base_pass_count}/{total_q}",
            "final_grounding_pass": f"{final_pass_count}/{total_q}",
            "baseline_numerical_valid": f"{base_num_pass}/{total_q}",
            "final_numerical_valid": f"{final_num_pass}/{total_q}",
            "baseline_avg_recall": round(base_avg_recall, 4),
            "final_avg_recall": round(final_avg_recall, 4),
        },
        "latency_stats_ms": {
            "total_ms": {
                "min": round(min(final_tot_latencies), 2),
                "max": round(max(final_tot_latencies), 2),
                "mean": round(statistics.mean(final_tot_latencies), 2),
                "median": round(statistics.median(final_tot_latencies), 2),
            },
            "qubo_ms": {
                "min": round(min(final_qubo_latencies), 2),
                "max": round(max(final_qubo_latencies), 2),
                "mean": round(statistics.mean(final_qubo_latencies), 2),
                "median": round(statistics.median(final_qubo_latencies), 2),
            },
            "student_generation_ms": {
                "min": round(min(final_student_latencies), 2),
                "max": round(max(final_student_latencies), 2),
                "mean": round(statistics.mean(final_student_latencies), 2),
                "median": round(statistics.median(final_student_latencies), 2),
            },
            "faiss_ms": {
                "min": round(min(final_faiss_latencies), 2),
                "max": round(max(final_faiss_latencies), 2),
                "mean": round(statistics.mean(final_faiss_latencies), 2),
                "median": round(statistics.median(final_faiss_latencies), 2),
            },
        },
        "baseline_results": baseline_results,
        "final_results": final_results,
    }

    out_json = Path(__file__).resolve().parent.parent.parent / "outputs" / "phase9_results.json"
    out_json.write_text(json.dumps(stats, indent=2), encoding="utf-8")

    print("\n" + "=" * 75)
    print("PHASE 9 EVALUATION SUMMARY")
    print("=" * 75)
    print(f"  Total Questions:                 {total_q}")
    print(f"  Baseline Grounding Pass Rate:    {base_pass_count}/{total_q} ({base_pass_count/total_q*100:.1f}%)")
    print(f"  Final Pipeline Grounding Pass:   {final_pass_count}/{total_q} ({final_pass_count/total_q*100:.1f}%)")
    print(f"  Final Numerical Preservation:    {final_num_pass}/{total_q} ({final_num_pass/total_q*100:.1f}%)")
    print(f"  Average Evidence Recall:         {final_avg_recall*100:.1f}%")
    print(f"  Mean Total Pipeline Latency:     {stats['latency_stats_ms']['total_ms']['mean']:.2f} ms")
    print(f"  Mean QUBO Optimization Latency:  {stats['latency_stats_ms']['qubo_ms']['mean']:.2f} ms")
    print(f"  Peak VRAM Footprint:             {stats['hardware']['peak_vram_mb']:.2f} MB")
    print(f"  Saved JSON Raw Results:          {out_json}")
    print("=" * 75)

    return stats


if __name__ == "__main__":
    run_phase9_evaluation()
