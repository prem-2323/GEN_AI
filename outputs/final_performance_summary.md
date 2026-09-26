# Final Performance Summary Report

## Executive Summary
This document summarizes the empirical performance metrics, memory footprint, and latency distributions measured across Phase 8 and Phase 9 evaluation benchmarks on the **DocLink Grounded RAG Platform**.

---

## 1. Measured System Latency Summary

| Pipeline Component | Minimum Latency | Maximum Latency | Mean Latency | Median Latency |
|---|---|---|---|---|
| **BGE Query Embedding** | 1.10 ms | 3.50 ms | 1.85 ms | 1.70 ms |
| **FAISS Vector Search** | 11.52 ms | 61.07 ms | 23.03 ms | 13.95 ms |
| **Neo4j Graph Search** | 4,055.10 ms | 4,211.36 ms | 4,082.50 ms | 4,073.95 ms |
| **RRF Candidate Fusion** | 0.00 ms | 0.75 ms | 0.28 ms | 0.00 ms |
| **QUBO Optimization Solver**| **3.83 ms** | **5.59 ms** | **4.56 ms** | **4.58 ms** |
| **Context Builder** | 0.00 ms | 0.08 ms | 0.03 ms | 0.00 ms |
| **QLoRA Student LLM** | 3,375.55 ms | 9,874.59 ms | **6,095.04 ms** | 5,812.94 ms |
| **Grounding Validator** | 0.00 ms | 1.20 ms | 0.80 ms | 0.70 ms |
| **Total Pipeline Latency** | **7,450.52 ms** | **14,153.11 ms** | **10,220.30 ms** | **9,891.04 ms** |

---

## 2. Ingestion Performance Summary

Target Document: `test sample/testreport.pdf` (10 pages, 47,972 chars, 127 semantic chunks)

- **PDF Text & Bounding Box Extraction**: 786.10 ms
- **BGE Batch Embedding Generation**: 764.46 ms
- **FAISS Index Insertion & Persistence**: 13.72 ms
- **Total Document Ingestion Time**: **25.12 seconds**

---

## 3. Hardware & VRAM Memory Footprint

- **GPU Accelerator**: NVIDIA GeForce RTX 3050 Laptop GPU (4 GB VRAM)
- **PyTorch / CUDA**: PyTorch `2.14.0+cu126`, CUDA `12.6`
- **Initial Allocated Memory**: 0.00 MB
- **Peak VRAM Allocated (Ingestion)**: 486.20 MB
- **Peak VRAM Allocated (Student Inference)**: **1,125.62 MB** (~1.12 GB VRAM)
- **VRAM Headroom**: **~2.87 GB free** out of 4 GB available VRAM limit.

---

## 4. Evaluation Quality Metrics

- **Grounded Answer Rate**: **100% (20 / 20 PASS)**
- **Numerical Fact Preservation**: **100% (20 / 20 PASS)**
- **Citation Validity**: **100%** (Zero invalid citation references)
- **Regression Test Suite**: **59 passed, 0 failed, 0 skipped** (100% PASS)
- **Frontend Production Build**: **PASS** (Built cleanly in 8.29 seconds)
