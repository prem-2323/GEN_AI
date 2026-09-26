# DocLink System Architecture Diagram

## System Architecture

```
                                    ┌────────────────────────────────┐
                                    │      React + Vite Frontend     │
                                    │    (http://localhost:5173)     │
                                    └───────────────┬────────────────┘
                                                    │
                                                    ▼  POST /api/rag/answer
                                    ┌────────────────────────────────┐
                                    │      FastAPI Backend Core      │
                                    │    (http://localhost:8000)     │
                                    └───────────────┬────────────────┘
                                                    │
                                                    ▼
                                    ┌────────────────────────────────┐
                                    │ PyMuPDF Extraction & Chunker   │
                                    └───────────────┬────────────────┘
                                                    │
                                ┌───────────────────┴───────────────────┐
                                │                                       │
                                ▼ [REAL]                                ▼ [REAL]
                 ┌─────────────────────────────┐         ┌─────────────────────────────┐
                 │ Neo4j Knowledge Graph       │         │ BGE-Small-EN-v1.5 Embedder  │
                 │ (Entities, Facts, Relations)│         │ (384-dimensional CUDA dense)│
                 └──────────────┬──────────────┘         └──────────────┬──────────────┘
                                │                                       │
                                │                                       ▼ [REAL]
                                │                        ┌─────────────────────────────┐
                                │                        │ Persistent FAISS Store      │
                                │                        │ (IndexFlatIP vector index)  │
                                │                        └──────────────┬──────────────┘
                                │                                       │
                                └───────────────────┬───────────────────┘
                                                    │
                                                    ▼ [REAL]
                                    ┌────────────────────────────────┐
                                    │ Reciprocal Rank Fusion (RRF)   │
                                    │  (Candidate Fusion k=60)       │
                                    └───────────────┬────────────────┘
                                                    │
                                                    ▼ [REAL CLASSICAL]
                                    ┌────────────────────────────────┐
                                    │ REAL QUBO Optimization Solver  │
                                    │ (Exact / Simulated Annealing)  │
                                    └───────────────┬────────────────┘
                                                    │ (Optional Future Link: Quantum Backend)
                                                    ▼ [REAL]
                                    ┌────────────────────────────────┐
                                    │ Grounded Context Builder       │
                                    │   (Manifest [E1], [E2]...)     │
                                    └───────────────┬────────────────┘
                                                    │
                                                    ▼ [REAL]
                                    ┌────────────────────────────────┐
                                    │ QLoRA Fine-Tuned Student LLM   │
                                    │  (Qwen/Qwen2.5-0.5B-Instruct)  │
                                    └───────────────┬────────────────┘
                                                    │
                                                    ▼ [REAL]
                                    ┌────────────────────────────────┐
                                    │ Grounding & Fact Validator     │
                                    │  (Exact Numerical Check)       │
                                    └───────────────┬────────────────┘
                                                    │
                                                    ▼
                                    ┌────────────────────────────────┐
                                    │ Grounded Answer + Citations UI │
                                    └────────────────────────────────┘
```

---

## Service Implementation Status Legend

- **[REAL]**: Production component active and verified (Neo4j, BGE, FAISS, RRF, QLoRA Student, Grounding Validator).
- **[REAL CLASSICAL]**: QUBO binary matrix formulation solved using classical Exact Binary & Simulated Annealing algorithms.
- **[FUTURE / OPTIONAL]**: Direct integration with hardware Quantum Annealers (D-Wave / Qiskit) via $Q$-matrix.
- **[BLOCKED]**: Ollama Qwen3 Teacher distillation (Not a runtime dependency).
