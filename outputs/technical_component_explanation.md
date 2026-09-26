# Technical Component Explanation & Theoretical Framework

## Executive Summary
This document provides deep technical explanations of each core component in the **DocLink Grounded RAG Platform**, explaining why each technology was chosen, its mathematical formulation, and its operational benefit.

---

## 1. Neo4j Knowledge Graph
- **Why Graph Relationships?**: Vector embeddings capture text semantic similarity, but fail to explicitly represent multi-hop structural relationships (e.g. *Which sensor measures temperature on the ESP32 board mentioned on page 4?*). Neo4j maintains explicit `:Entity`, `:Fact`, and `:Document` nodes with typed relationships (`:CONTAINS`, `:MEASURES`, `:EVALUATED_BY`).
- **Parameterized Cypher Execution**: Queries use strict parameterized syntax to enforce deterministic sub-graph matching and prevent Cypher injection risks.

---

## 2. BAAI/bge-small-en-v1.5 Semantic Embeddings
- **Why BGE Embeddings?**: BAAI/bge-small-en-v1.5 is a top-performing 384-dimensional dense retrieval embedding model on MTEB benchmarks. It produces compact vectors that execute efficiently on GPU while maintaining high semantic retrieval precision.
- **Normalization**: L2 normalization ensures inner product dot similarity is mathematically identical to cosine similarity.

---

## 3. Persistent FAISS Vector Store (`FAISSVectorStore`)
- **Why FAISS?**: Facebook AI Similarity Search (FAISS) enables ultra-low latency sub-50ms vector search. `IndexFlatIP` stores dense floating-point vectors in contiguous memory arrays, achieving maximum hardware throughput on CPU AVX2 and GPU CUDA.

---

## 4. Reciprocal Rank Fusion (RRF)
- **Why RRF Fusion?**: Vector similarity and graph relationships produce scores on non-comparable scales (similarity logits vs graph path weights). RRF combines distinct rankings into a unified score without score calibration:
  $$S_{\text{RRF}}(c) = \frac{1}{k + R_{\text{vector}}(c)} + \frac{1}{k + R_{\text{graph}}(c)} \quad (k=60)$$

---

## 5. QUBO Evidence Selection Optimization
- **Why QUBO?**: Standard top-$K$ retrieval selects the highest-scoring individual chunks, often introducing redundant overlapping text into prompt context. QUBO formulates evidence subset selection as a Quadratic Unconstrained Binary Optimization matrix problem:
  $$\min_{x \in \{0,1\}^N} x^T Q x = \sum_{i=1}^N q_{ii} x_i + \sum_{i < j} q_{ij} x_i x_j$$
  - **Diagonal Terms ($q_{ii}$)**: Negative rewards for candidate relevance, graph connectivity, and source quality ($x_i = 1$).
  - **Off-Diagonal Terms ($q_{ij}$)**: Positive penalties for text redundancy and overlapping information between candidates $i$ and $j$.
  - **Cardinality Constraint**: Soft penalty $( \sum x_i - K )^2$ enforcing target evidence subset count $K$.

---

## 6. Fine-Tuned QLoRA Student LLM (`Qwen/Qwen2.5-0.5B-Instruct`)
- **Why QLoRA Student?**: A 0.5B parameter instruction-tuned LLM fine-tuned with PEFT LoRA adapters fits comfortably in under **1.2 GB VRAM**, enabling full local GPU inference on standard laptop GPUs (RTX 3050 4 GB) without requiring cloud API keys.

---

## 7. Deterministic Grounding Validator
- **Why Deterministic Validation?**: LLM output evaluation should not depend on another ungrounded LLM. The grounding validator deterministically extracts cited evidence IDs `[E1], [E2]`, verifies citation existence in prompt manifest, and matches extracted numerical facts against source text.
