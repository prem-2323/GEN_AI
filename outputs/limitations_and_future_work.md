# Limitations & Future Work Specification

## Executive Summary
This document provides a transparent record of all current system limitations, constraints, blocked dependencies, and future architectural roadmaps for the **DocLink Grounded RAG Platform**.

---

## 1. Documented System Limitations

### 1.1 Teacher Model Qwen3 Distillation: BLOCKED
- **Status**: **BLOCKED**
- **Root Cause**: Local Ollama service experienced GPU initialization failures on Windows environment.
- **Impact**: System operates independently using the pre-distilled fine-tuned QLoRA student model checkpoint (`Qwen/Qwen2.5-0.5B-Instruct` + `outputs/distillation/student`). Teacher Qwen3 generation is not a runtime dependency.

### 1.2 Quantum Hardware Integration: NOT CONNECTED
- **Status**: **NOT CONNECTED**
- **Implementation**: QUBO evidence selection matrix $x^T Q x$ is solved using classical Exact Binary Search and classical Simulated Annealing solvers (`solvers.py`).
- **Clarification**: Simulated annealing is a classical probabilistic algorithm. No claims of quantum hardware execution are made.

### 1.3 Hardware & VRAM Constraints
- **Target Hardware**: NVIDIA GeForce RTX 3050 Laptop GPU with 4 GB VRAM.
- **Constraint Handling**: Student LLM model footprint is strictly bounded to $\le 1.2$ GB VRAM. Concurrent loading of multiple heavy LLM instances is avoided.

### 1.4 Scalability of Exact QUBO Solver
- **Exact Solver Limit**: Exact binary search evaluates $2^N$ candidate states and is bounded to candidate pools $N \le 20$.
- **Large Candidate Handling**: Simulated Annealing is automatically invoked for candidate pools $N > 20$.

### 1.5 Multi-Document Evaluation Scope
- **Evaluation Limitation**: Primary evaluation dataset utilizes `test sample/testreport.pdf` (127 chunks). Multi-document isolation is verified via metadata scoping unit tests (`test_faiss_vector_store.py`).

---

## 2. Future Work & Roadmap

```
Current Architecture:
  QUBO Matrix formulation ($x^T Q x$) ➔ Classical Exact / Simulated Annealing Solvers

Future Quantum Architecture:
  QUBO Matrix formulation ($x^T Q x$) ➔ Quantum Cloud API (D-Wave Leap / Qiskit) ➔ Hardware Quantum Annealer
```

1. **Hardware Quantum Backend**: Connect the binary QUBO matrix $Q$ to physical D-Wave Advantage quantum annealers via `dwave-system` SDK.
2. **Multi-Modal Document Processing**: Expand layout extraction to chart images, diagrams, and scanned OCR using vision LLM adapters.
3. **Dynamic Graph Ontology Learning**: Automatically infer custom Cypher entity relationship schemas from novel document domains.
