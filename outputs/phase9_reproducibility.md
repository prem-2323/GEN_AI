# Phase 9 — Reproducibility & Benchmark Environment Specification

## Executive Summary
This document records the exact configuration, software dependencies, model parameters, seed settings, and hardware environment required to independently reproduce all Phase 9 evaluation benchmarks.

---

## 1. Environment & Software Stack

- **Operating System**: Windows 11 Home / Pro (64-bit)
- **Python Version**: 3.11.9 (`C:\Users\premk\AppData\Local\Programs\Python\Python311\python.exe`)
- **Node.js / npm**: Node v18+ / npm v10+
- **PyTorch Version**: 2.14.0+cu126 (CUDA 12.6 support enabled)
- **FastAPI Version**: 0.110+
- **FAISS Version**: `faiss-cpu` / `faiss-gpu` v1.8.0
- **PEFT / bitsandbytes**: Installed and configured for 4-bit / float16 LoRA loading

---

## 2. Hardware Acceleration

- **GPU Accelerator**: NVIDIA GeForce RTX 3050 Laptop GPU
- **VRAM Capacity**: 4,096 MB (4 GB)
- **CUDA Device Index**: `cuda:0`

---

## 3. Model Configuration & Checkpoints

- **Embedding Model**:
  - Model Name: `BAAI/bge-small-en-v1.5`
  - Source: HuggingFace Hub
  - Embedding Dimension: 384
  - Normalization: L2 Normalized Cosine Similarity
- **QLoRA Student LLM**:
  - Base Model: `Qwen/Qwen2.5-0.5B-Instruct`
  - PEFT Adapter Path: `outputs/distillation/student`
  - Quantization / Dtype: Float16 / Auto
  - Max New Tokens: 128 (Benchmarking) / 256 (Production)

---

## 4. QUBO Optimization Matrix Settings

- **Formulation**: Quadratic Unconstrained Binary Optimization ($x^T Q x$)
- **Solver Type**: `exact` (Brute-force binary solver for $N \le 20$) / `simulated_annealing`
- **Objective Weights**:
  - $\alpha$ (Relevance Reward): 0.5
  - $\beta$ (Graph/Structure Reward): 0.3
  - $\gamma$ (Redundancy Penalty): 0.2
  - $\lambda$ (Cardinality Penalty): 1.0
- **Random Seed**: `42` (Fixed PyTorch and NumPy seed)

---

## 5. Execution Command

To reproduce the complete evaluation dataset benchmark:
```bash
python Backend/tests/benchmark_phase9.py
```
Output data will be written to: `outputs/phase9_results.json`.
