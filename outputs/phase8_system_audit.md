# Phase 8 — System Audit Report

## Executive Summary
This document provides a comprehensive audit of the **Document Intelligence / DocLink** system architecture, including backend APIs, frontend components, vector & graph databases, optimization solvers, and model integration.

---

## 1. Current Architecture Overview
The system follows a multi-tier hybrid architecture for Document Intelligence & RAG:

```
[ PDF Document ] -> [ Extraction Engine ] -> [ Neo4j Knowledge Graph & FAISS Vector Index ]
                                                          │
[ User Query ] ──> [ Hybrid Graph+Vector Retrieval ] ────┘
                          │
                          ▼
             [ RRF Reciprocal Rank Fusion ]
                          │
                          ▼
             [ QUBO Evidence Selection (Exact / SA) ]
                          │
                          ▼
             [ QLoRA Student LLM (Qwen2.5-0.5B-Instruct) ]
                          │
                          ▼
             [ Numerical & Grounding Validator ] ──> [ Answer + Citations ]
```

---

## 2. Backend Inventory

- **Framework**: FastAPI (Python 3.10+)
- **Entry Point**: `Backend/app/main.py`
- **Core Modules**:
  - `Backend/app/rag/grounded_rag.py`: Grounded RAG orchestrator integrating retrieval, QUBO, student inference, and verification.
  - `Backend/app/optimization/solvers.py`: Classical Exact and Simulated Annealing solvers for QUBO formulation.
  - `Backend/app/rag/student_model.py`: QLoRA student model wrapper (`Qwen/Qwen2.5-0.5B-Instruct` + peft adapter).
  - `Backend/app/rag/hybrid_retrieval.py`: Hybrid Neo4j Cypher graph search + BGE FAISS vector search + RRF fusion.
  - `Backend/app/graph/neo4j_client.py`: Neo4j graph client (`GRAPH_BACKEND=neo4j`).
  - `Backend/app/embeddings/bge_embeddings.py`: BAAI/bge-small-en-v1.5 embedding generator.
  - `Backend/app/vectorstore/faiss_store.py`: Persistent FAISS vector store.
  - `Backend/app/verification/grounding_validator.py`: Numerical fact verification & ground truth check.

---

## 3. Frontend Inventory

- **Framework**: React 18 + Vite + TypeScript + TailwindCSS
- **Entry Point**: `Frontend/src/main.tsx` / `Frontend/src/App.tsx`
- **Services & APIs**:
  - `Frontend/src/services/backendService.ts`: Core API client for backend routes.
  - `Frontend/src/api/ragApi.ts`: Grounded RAG query handler (`POST /api/rag/answer`).
  - `Frontend/src/components/results/RagSearchModal.tsx`: Grounded RAG user interface.

---

## 4. API Routes Summary

| Path | Method | Module | Description |
|---|---|---|---|
| `/health` | GET | `health.py` | Core server health check |
| `/api/graph/health` | GET | `graph.py` | Neo4j connection health |
| `/api/graph/status` | GET | `graph.py` | Neo4j node/edge counts & status |
| `/api/embeddings/status` | GET | `embeddings.py` | BGE embedding model & CUDA status |
| `/api/qubo/status` | GET | `qubo.py` | QUBO solver availability & config |
| `/api/student/status` | GET | `student.py` | QLoRA student model status |
| `/api/rag/answer/status` | GET | `rag.py` | Grounded RAG pipeline status |
| `/api/rag/answer` | POST | `rag.py` | Main grounded RAG question answering endpoint |
| `/api/upload` | POST | `upload.py` | File upload endpoint |
| `/api/pipeline/process` | POST | `pipeline.py` | Document ingestion & indexing pipeline |

---

## 5. Important Environment Variables

- `NEO4J_URI`: Neo4j connection string (default: `bolt://localhost:7687`)
- `NEO4J_USERNAME`: Neo4j user (default: `neo4j`)
- `NEO4J_PASSWORD`: Neo4j password (default: `doclink123`)
- `GRAPH_BACKEND`: `neo4j` (Real Neo4j mode)
- `EMBEDDING_MODEL_NAME`: `BAAI/bge-small-en-v1.5`
- `FAISS_STORAGE_DIR`: `storage/faiss_index`
- `STUDENT_MODEL_PATH`: `Qwen/Qwen2.5-0.5B-Instruct`
- `STUDENT_ADAPTER_PATH`: `outputs/distillation/student`

---

## 6. Dependencies & Services Status

| Component | Status | Implementation |
|---|---|---|
| **Neo4j Graph DB** | REAL / READY | Neo4j Enterprise/Community v5+ running locally |
| **BGE Embeddings** | REAL / READY | BAAI/bge-small-en-v1.5 (384 dim, PyTorch CUDA/CPU) |
| **FAISS Vector DB** | REAL / READY | Persistent `IndexFlatIP` vector index |
| **QUBO Optimization**| REAL / READY | Exact & Simulated Annealing solvers (`solvers.py`) |
| **QLoRA Student** | REAL / READY | Qwen2.5-0.5B-Instruct + PEFT adapter |
| **Grounding Verification**| REAL / READY | Fact verification & regex/numerical checker |
| **Teacher Qwen3** | BLOCKED | Ollama GPU initialization failure (Not a blocker) |
| **Quantum Hardware**| NOT CONNECTED| Classical QUBO emulation active |

---

## 7. Known Blockers & Demo Risks

1. **VRAM Constraints**: 4 GB VRAM (RTX 3050 Laptop). QLoRA student loaded in 4-bit / 8-bit / float16 mode safely consumes ~1.8 GB VRAM. No additional heavy models should be loaded concurrently.
2. **Teacher Qwen3 Generation**: Ollama teacher service is unavailable on local GPU; system uses validated distillation dataset and QLoRA student fine-tuned checkpoint.
3. **Frontend Integration Sync**: Ensure frontend correctly formats source citations ([E1], [E2]), displays QUBO evidence selection metrics, and visualizes grounding pass/fail status.
