# ⚡ DocLink — Enterprise Document Intelligence & Grounded Multi-Channel Transformation Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.3+-61DAFB.svg?logo=react)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-5.4+-646CFF.svg?logo=vite)](https://vitejs.dev/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.0+-008CC1.svg?logo=neo4j)](https://neo4j.com/)
[![FAISS](https://img.shields.io/badge/FAISS-Vector%20Store-green.svg)](https://github.com/facebookresearch/faiss)
[![PyTorch](https://img.shields.io/badge/PyTorch-CUDA%20Accelerated-EE4C2C.svg?logo=pytorch)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**DocLink** (Gen-Transform AI) is an enterprise-grade Document Intelligence, Knowledge Graph Synthesis, and Grounded Multi-Channel Deliverable Generation Platform. It bridges the gap between unstructured document silos and authoritative enterprise decision-making by combining **Dual-Channel Hybrid Retrieval (Neo4j Graph + FAISS Dense Vector)**, **Reciprocal Rank Fusion (RRF)**, **QUBO Mathematical Evidence Selection Optimization**, **Fine-Tuned QLoRA Student LLMs**, and **Deterministic Grounding & Numerical Verification**.

---

## 📑 Table of Contents

1. [Platform Overview & Core Capabilities](#-platform-overview--core-capabilities)
2. [Service Implementation Matrix](#-service-implementation-matrix)
3. [Global End-to-End System Architecture](#-global-end-to-end-system-architecture)
4. [Subsystem Deep-Dives (Separate Architectures)](#-subsystem-deep-dives-separate-architectures)
   - [4.1 Multi-Modal Ingestion & Document Extraction](#41-multi-modal-ingestion--document-extraction-subsystem)
   - [4.2 FAISS Dense Vector Database & Embeddings](#42-faiss-dense-vector-database--embeddings-subsystem)
   - [4.3 Neo4j Knowledge Graph & Entity Relationships](#43-neo4j-knowledge-graph--entity-relationships-subsystem)
   - [4.4 Hybrid RAG & Reciprocal Rank Fusion (RRF)](#44-hybrid-rag--reciprocal-rank-fusion-rrf-subsystem)
   - [4.5 QUBO Optimization & Evidence Selection Solver](#45-qubo-optimization--evidence-selection-solver-subsystem)
   - [4.6 Knowledge Distillation & QLoRA Student LLM](#46-knowledge-distillation--qlora-student-llm-subsystem)
   - [4.7 Universal Cyber Knowledge Representation (UCKR)](#47-universal-cyber-knowledge-representation-uckr-subsystem)
   - [4.8 Multi-Channel Deliverable Transformation Engine](#48-multi-channel-deliverable-transformation-engine)
   - [4.9 Grounding & Numerical Verification Engine](#49-grounding--numerical-verification-engine)
   - [4.10 Cryptographic Provenance Ledger & Audit Trail](#410-cryptographic-provenance-ledger--audit-trail)
5. [End-to-End Processing Workflow](#-end-to-end-processing-workflow)
6. [Tech Stack & Dependencies](#-tech-stack--dependencies)
7. [Prerequisites & System Requirements](#-prerequisites--system-requirements)
8. [Installation & Setup](#-installation--setup)
9. [Configuration & Environment Variables (`.env`)](#-configuration--environment-variables-env)
10. [Starting Services (Run Guide)](#-starting-services-run-guide)
11. [REST API Endpoint Catalog](#-rest-api-endpoint-catalog)
12. [Automated Test Suite & Benchmarks](#-automated-test-suite--benchmarks)
13. [Performance Metrics & Resource Footprint](#-performance-metrics--resource-footprint)
14. [Security, Concurrency & Data Integrity](#-security-concurrency--data-integrity)

---

## 🌟 Platform Overview & Core Capabilities

Enterprise organizations process dense technical reports, vulnerability advisories, compliance audits, and architectural specifications. Traditional LLM pipelines suffer from high hallucination rates, lost context in multi-hop entity relations, and arbitrary context window clipping.

DocLink solves these challenges through a hardened 10-phase pipeline:
1. **Multi-Format Extraction**: Parses PDF, DOCX, TXT, Markdown, and images into normalized structural ASTs with exact page and section citations.
2. **Dual-Channel Indexing**: Simultaneously maps text embeddings into a persistent **FAISS** vector store and structured entity-relation networks into a **Neo4j** knowledge graph.
3. **Universal Cyber Knowledge Representation (UCKR)**: Synthesizes facts, vulnerabilities (CVEs), technical metrics (CVSS, latencies), attack vectors, and mitigations into a unified semantic graph.
4. **Hybrid RAG with Reciprocal Rank Fusion (RRF)**: Combines dense vector semantics ($R_{\text{vec}}$) and structural graph connectivity ($R_{\text{graph}}$) at $k=60$.
5. **QUBO Evidence Selection**: Converts candidate chunk selection into a Quadratic Unconstrained Binary Optimization problem ($x^T Q x$) that maximizes relevance and diversity while eliminating redundant noise.
6. **Edge-Efficient QLoRA Student Model**: Runs a fine-tuned lightweight LLM (`Qwen2.5-0.5B-Instruct` + QLoRA adapter) with a tiny VRAM footprint (~1.12 GB VRAM).
7. **Deterministic Grounding & Numerical Fact-Checking**: Automatically validates all generated claims, metrics, and citations against source ground-truth chunks before rendering.
8. **Multi-Channel Enterprise Deliverables**: Instantly generates Executive Summaries, Technical Engineering Runbooks, C-Suite Presentations (PPTX/Markdown), Social/Slack Briefings, and Audio Briefing scripts.
9. **Full Cryptographic Provenance**: Every sentence, claim, and deliverable metric is cryptographically linked via SHA-256 hashes to its exact document chunk source.

---

## 📊 Service Implementation Matrix

| Subsystem / Service | Implementation Status | Technical Engine / Hardware |
| :--- | :--- | :--- |
| **Document Ingestion Engine** | **REAL / PRODUCTION** | PyMuPDF, `pypdf`, `python-docx`, Tesseract/OCR Fallback |
| **Dense Semantic Embeddings** | **REAL / PRODUCTION** | `BAAI/bge-small-en-v1.5` (384-dim, CUDA accelerated) |
| **Vector Database** | **REAL / PRODUCTION** | Persistent FAISS `IndexFlatIP` (Disk persistence at `storage/vector_db/`) |
| **Knowledge Graph Database** | **REAL / PRODUCTION** | Neo4j v5+ parameterized Cypher (`bolt://localhost:7687`) + Mock fallback |
| **Hybrid Retrieval & RRF** | **REAL / PRODUCTION** | Dual-channel search fusion ($k=60$) |
| **QUBO Optimization Solver** | **REAL / PRODUCTION** | Classical Exact Binary & Simulated Annealing solvers ($x^T Q x$) |
| **QLoRA Student LLM** | **REAL / PRODUCTION** | `Qwen/Qwen2.5-0.5B-Instruct` + PEFT LoRA adapter |
| **Grounding & Fact Validator** | **REAL / PRODUCTION** | Deterministic regex parsing & exact numerical reconciliation |
| **Document Repository Store** | **REAL / PRODUCTION** | Local thread-safe JSON repository (`JSONDocumentRepository`) |
| **Quantum Hardware Link** | **FORMULATED** | Standard QUBO $Q$-matrix output ready for D-Wave / Qiskit annealers |
| **Teacher Qwen3 Generation** | **OFFLINE FALLBACK** | Local Gemini / deterministic fallback when Ollama GPU is offline |

---

## 🏗️ Global End-to-End System Architecture

```
                                 ┌─────────────────────────────────────────────────────────┐
                                 │                   REACT + VITE FRONTEND                 │
                                 │       (Dashboard, Upload, Graph Explorer, RAG Search)   │
                                 └────────────────────────────┬────────────────────────────┘
                                                              │ HTTP REST / Multipart
                                                              ▼
                                 ┌─────────────────────────────────────────────────────────┐
                                 │                   FASTAPI BACKEND CORE                  │
                                 │               (App Orchestrator & API Router)           │
                                 └─────────────┬─────────────────────────────┬─────────────┘
                                               │                             │
                     ┌─────────────────────────┴──────────┐                  │
                     │ Ingestion & Extraction Pipeline    │                  │
                     │ (PyMuPDF, docx, normalizer)        │                  │
                     └─────────────┬──────────────────────┘                  │
                                   │                                         │
        ┌──────────────────────────┴──────────────────────────┐              │
        ▼                                                     ▼              ▼
┌─────────────────────────────┐                         ┌─────────────────────────────┐
│    Neo4j Knowledge Graph    │                         │   Persistent FAISS Store    │
│  (Entities, Facts, Edges)   │                         │  (BAAI/bge-small 384-dim)   │
└──────────────┬──────────────┘                         └──────────────┬──────────────┘
               │                                                       │
               │               ┌───────────────────────┐               │
               └──────────────►│ Hybrid Query Analyzer │◄──────────────┘
                               └───────────┬───────────┘
                                           │
                                           ▼
                               ┌───────────────────────┐
                               │ Reciprocal Rank Fusion│
                               │      (RRF k=60)       │
                               └───────────┬───────────┘
                                           │ Top-N Candidates
                                           ▼
                               ┌───────────────────────┐
                               │ QUBO Binary Matrix    │
                               │  Optimization Solver  │
                               │   (min x^T Q x)       │
                               └───────────┬───────────┘
                                           │ Optimal Subset {x_i = 1}
                                           ▼
                               ┌───────────────────────┐
                               │ Grounded Context      │
                               │ Builder ([E1], [E2])  │
                               └───────────┬───────────┘
                                           │
                                           ▼
                               ┌───────────────────────┐
                               │ QLoRA Student Model   │
                               │(Qwen2.5-0.5B-Instruct)│
                               └───────────┬───────────┘
                                           │ Raw Generated Content
                                           ▼
                               ┌───────────────────────┐
                               │ Grounding & Numerical │
                               │  Verification Engine  │
                               └───────────┬───────────┘
                                           │ Validated Deliverables + Citations
                                           ▼
                               ┌───────────────────────┐
                               │ JSON Document Stores  │
                               │ & Provenance Ledger   │
                               └───────────────────────┘
```

---

## 🧩 Subsystem Deep-Dives (Separate Architectures)

### 4.1 Multi-Modal Ingestion & Document Extraction Subsystem
Handles document upload, MIME verification, path sanitization, format-specific parsing, and text normalization.

```
[ Uploaded File: PDF / DOCX / TXT / MD ]
                  │
                  ▼
       [ Filename & MIME Sanitizer ] ──► (Path traversal & extension checks)
                  │
        ┌─────────┴──────────────────────────────┐
        ▼                                        ▼
 [ PyMuPDF / pypdf ]                   [ python-docx Parser ]
 (Text, Pages, Bounding Boxes, Img)     (Headings, Paragraphs, Tables)
        │                                        │
        └─────────────────┬──────────────────────┘
                          │
                          ▼
            [ Text Normalizer & AST Builder ]
       (Removes artifacts, fixes unicode, computes SHA-256)
                          │
                          ▼
              [ ExtractedDocument Model ]
    ├── metadata.json (file stats, page counts, hashes)
    └── text.json     (normalized chunks, sections, tables)
```

- **Supported Formats**: `.pdf`, `.docx`, `.doc`, `.txt`, `.md`, `.png`, `.jpg`, `.jpeg`.
- **Storage Layout**:
  - `storage/documents/<doc_id>/original/<filename>` (Raw binary)
  - `storage/documents/<doc_id>/extracted/text.json` (Structured chunks)
  - `storage/documents/<doc_id>/extracted/metadata.json` (Metadata sidecar)

---

### 4.2 FAISS Dense Vector Database & Embeddings Subsystem
Responsible for transforming normalized document chunks into dense mathematical vector spaces for sub-millisecond semantic search.

```
[ Document Chunks (C_1, C_2, ... C_N) ]
                  │
                  ▼
 [ BAAI/bge-small-en-v1.5 Embedding Model ]
 (CUDA / PyTorch Tensor Processing -> 384-dim Float32)
                  │
                  ▼
        [ L2 Vector Normalization ] ──► (||v||_2 = 1.0 for Cosine Metric)
                  │
                  ▼
         [ FAISS IndexFlatIP ]
 ├── faiss.index   (Flat Inner Product binary matrix)
 └── metadata.json (Chunk ID ↔ FAISS vector index map + text payload)
```

- **Vector Dimension**: 384 dimensions.
- **Metric**: Inner Product (`IndexFlatIP`) on normalized vectors $\equiv$ Cosine Similarity.
- **Thread Safety**: All mutations guarded by `threading.RLock()`.

---

### 4.3 Neo4j Knowledge Graph & Entity Relationships Subsystem
Extracts entities, concepts, relationships, vulnerabilities, and metrics from ingested documents to build a connected knowledge graph.

```
[ Extracted Document Chunks & Analysis ]
                  │
                  ▼
       [ Entity & Relation Extractor ]
 ├── Nodes: Document, Chunk, Entity, Vulnerability, Metric, Event
 └── Edges: CONTAINS, MENTIONS, TARGETS, MITIGATES, HAS_METRIC
                  │
                  ▼
     [ Parameterized Cypher Transactor ]
 (MATCH / MERGE statements via Neo4j Bolt Driver)
                  │
                  ▼
      [ Live Neo4j Graph Database ] (Port 7687)
```

- **Node Types**: `Document`, `Chunk`, `Entity`, `Concept`, `Vulnerability` (CVE), `Metric`, `Mitigation`.
- **Relationship Traversal**: Multi-hop graph neighborhood expansion up to depth $d=2$.

---

### 4.4 Hybrid RAG & Reciprocal Rank Fusion (RRF) Subsystem
Fuses dense semantic similarity with graph topology to ensure high recall across both conceptual queries and multi-hop entity inquiries.

```
                  [ User RAG Query ]
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
[ FAISS Vector Top-K Search ]  [ Neo4j Graph Traversal & Search ]
  Scores: S_vec(c_i)             Scores: S_graph(c_i)
  Ranks:  R_vec(c_i)             Ranks:  R_graph(c_i)
             │                           │
             └─────────────┬─────────────┘
                           ▼
          [ Reciprocal Rank Fusion (RRF) ]
       S_RRF(c) = 1/(60 + R_vec(c)) + 1/(60 + R_graph(c))
                           │
                           ▼
          [ Top-M Fused Candidate Pool ]
```

---

### 4.5 QUBO Optimization & Evidence Selection Solver Subsystem
Selects the optimal subset of evidence chunks to inject into the LLM context by formulating evidence selection as a Quadratic Unconstrained Binary Optimization (QUBO) problem.

$$\min_{x \in \{0,1\}^N} E(x) = x^T Q x = -\sum_{i=1}^N r_i x_i + \lambda_{\text{sim}} \sum_{i < j} S_{ij} x_i x_j + \lambda_{\text{budget}} \left( \sum_{i=1}^N x_i - K \right)^2$$

```
[ Fused Candidates (C_1...C_N) ] + [ Query Vector ]
                  │
                  ▼
        [ QUBO Matrix Formulator ]
 ├── Diagonal Q_ii: Relevance score -r_i - 2*lambda_budget*K + lambda_budget
 └── Off-Diagonal Q_ij: Redundancy penalty S_ij + 2*lambda_budget
                  │
                  ▼
   [ Classical Optimization Solvers ]
 ├── Exact Binary Exhaustive Solver (N <= 20)
 └── Simulated Annealing Solver     (N > 20)
                  │
                  ▼
     [ Optimal Binary Vector x* ] ──► (Selects high-relevance, diverse chunks)
                  │
                  ▼
  [ Manifest Context: [E1], [E2], ... [EK] ]
```

---

### 4.6 Knowledge Distillation & QLoRA Student LLM Subsystem
Enables fast, low-latency, fully on-device inference by distilling reasoning capabilities into an efficient student model.

```
       [ Teacher Model: Qwen3 / Gemini ]
                       │
                       ▼
          [ Distillation Dataset ]
  (100+ Triples: {Context, Query, Grounded Answer})
                       │
                       ▼
   [ Parameter-Efficient Fine-Tuning (PEFT) ]
  Base: Qwen/Qwen2.5-0.5B-Instruct
  LoRA Rank (r): 16 | Alpha: 32 | Dropout: 0.05
                       │
                       ▼
  [ QLoRA Student Checkpoint: outputs/distillation/student ]
  (VRAM Footprint: ~1.12 GB | Inference Latency: 3.3s - 9.8s)
```

---

### 4.7 Universal Cyber Knowledge Representation (UCKR) Subsystem
Serves as the single source of truth across all deliverable generation channels.

```
[ Extracted AST + Analysis ] ──► [ UCKR Synthesizer ]
                                        │
     ┌──────────────────────────────────┴──────────────────────────────────┐
     ▼                                  ▼                                  ▼
[ Executive Overview ]         [ Threat & Incident Model ]       [ Technical Metrics ]
- Title & Author               - Threat Actors                   - CVSS Scores
- Incident Summary             - Affected Systems                - Latency Delays
- Business Impact              - Attack Vectors & CVEs           - Financial Impact
```

---

### 4.8 Multi-Channel Deliverable Transformation Engine
Transforms the centralized UCKR data into tailored enterprise artifacts.

```
                                  [ Central UCKR Schema ]
                                             │
      ┌───────────────────┬──────────────────┼───────────────────┬───────────────────┐
      ▼                   ▼                  ▼                   ▼                   ▼
[ Executive Brief ]  [ Tech Runbook ]  [ C-Suite PPTX ]   [ Slack / Social ]  [ Audio Briefing ]
  Markdown/PDF         Markdown/Code     16:9 Presentation  Short-form Bullet   Spoken Audio Script
  Executive Summary    Root Cause & Fix  Slides & Visuals   Updates & Alerts    with Pronunciation
```

---

### 4.9 Grounding & Numerical Verification Engine
A zero-tolerance deterministic validator that scans generated outputs to prevent LLM hallucinations.

```
[ Generated Deliverable Content ] + [ Ground Truth Extracted Document ]
                          │
                          ▼
            [ Grounding Verification Scanner ]
 ├── Regex Numerical Scanner: Extracts all numbers, percentages, CVEs, CVSS scores
 ├── Exact Match Reconciliation: Checks presence of every metric in source text
 └── Citation Boundary Check: Ensures all [E1], [E2] references map to real chunks
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
      [ 100% Pass Rate ]       [ Discrepancy Flag ]
      Render & Export Output    Flagged in UI with warning badges
```

---

### 4.10 Cryptographic Provenance Ledger & Audit Trail
Maintains complete regulatory auditability for every claim generated.

```
[ Source Chunk C_i ] ── SHA-256 ──► [ Chunk Hash H(C_i) ]
                                            │
                                            ▼
[ Generated Claim G_j ] ──────────► [ Provenance Record ]
                                    ├── Claim Text
                                    ├── Source Document ID & Page
                                    ├── Source Chunk SHA-256
                                    └── Timestamp & User ID
                                            │
                                            ▼
                               [ `data/provenance/records.json` ]
```

---

## 🔄 End-to-End Processing Workflow

```
[User Action: Uploads PDF/DOCX]
  │
  ├─► 1. Ingestion: Sanitizes file, saves raw binary to storage/documents/<doc_id>/original/
  ├─► 2. Extraction: PyMuPDF / docx extracts text, pages, tables -> storage/documents/<doc_id>/extracted/
  │
[System Action: Indexing Phase]
  ├─► 3. Vector Indexing: Generates 384-dim BGE embeddings -> Inserts into FAISS vector index
  ├─► 4. Graph Ingestion: Extracts entities and relationships -> Inserts into Neo4j Graph Database
  │
[System Action: Analysis & UCKR Synthesis]
  ├─► 5. AI Understanding: Identifies key facts, vulnerabilities, metrics, and incident timelines
  ├─► 6. UCKR Generation: Builds Universal Cyber Knowledge Representation model
  │
[User Action: Submits RAG Query or Requests Multi-Channel Transformation]
  ├─► 7. Dual Search: Queries FAISS (vector similarity) + Queries Neo4j (graph neighbors)
  ├─► 8. Fusion: RRF merges candidate lists into ranked pool (k=60)
  ├─► 9. Optimization: QUBO solver selects optimal subset of evidence manifest ([E1], [E2])
  ├─► 10. Generation: QLoRA Student LLM generates grounded answers or multi-channel deliverables
  ├─► 11. Verification: Grounding validator reconciles all numbers and citations against ground truth
  └─► 12. UI Render: Renders interactive UI with citation badges, graphs, and export options
```

---

## 💻 Tech Stack & Dependencies

### Frontend
- **Framework**: React 18 with TypeScript
- **Bundler & Tooling**: Vite 5.4+
- **Styling**: TailwindCSS & Vanilla CSS (Glassmorphism, CSS Custom Properties, Dark Mode)
- **Icons & UI**: Lucide React, Canvas API
- **State & API**: Custom React Hooks, Axios / Fetch API

### Backend Core
- **Framework**: FastAPI (Asynchronous Python 3.10 / 3.11)
- **Server**: Uvicorn ASGI Server
- **Data Validation**: Pydantic v2 Settings & Schemas
- **Logging**: Structured centralized logging (`app.core.logging`)

### AI Models & Vector Search
- **Embeddings**: `BAAI/bge-small-en-v1.5` (via `sentence-transformers` & HuggingFace Hub)
- **Vector Search Engine**: `faiss-cpu` (IndexFlatIP with cosine similarity)
- **Student LLM**: `Qwen/Qwen2.5-0.5B-Instruct`
- **Fine-Tuning Framework**: PyTorch, HuggingFace `transformers`, `peft` (QLoRA)

### Graph Database & Mathematical Solvers
- **Graph Database**: Neo4j Enterprise/Community v5+ (Python `neo4j` driver)
- **QUBO Solvers**: Exact Binary Exhaustive Solver, Simulated Annealing Optimization Solver, NumPy

### Document Parsing & File Generation
- **Parsers**: `PyMuPDF` (fitz), `pypdf`, `python-docx`, `python-pptx`, `chardet`, `reportlab`

---

## ⚙️ Prerequisites & System Requirements

- **Operating System**: Windows 10/11, Ubuntu 20.04+, or macOS
- **Python**: Version `3.10` or `3.11`
- **Node.js**: Version `18.0.0` or higher & `npm`
- **Memory (RAM)**: Minimum 8 GB RAM (16 GB recommended)
- **GPU Acceleration**: NVIDIA GPU with CUDA support (Minimum 4 GB VRAM for local student LLM inference). *Runs on CPU in CPU-only mode automatically if CUDA is unavailable.*
- **Graph Database**: Neo4j v5+ (Optional; system includes an automated mock repository fallback).

---

## 🚀 Installation & Setup

### 1. Clone Repository & Setup Virtual Environment
```bash
# Clone the repository
### Option A: One-Click Installation (Recommended)

#### On Windows (Command Prompt):
```cmd
install_all.bat
```

#### On PowerShell:
```powershell
.\install_all.ps1
```
*(Automatically checks prerequisites, upgrades pip, installs all Python packages from `Backend/requirements.txt`, runs `npm install` in `Frontend`, sets up `.env` from template, and initializes storage folders).*

---

### Option B: Manual Step-by-Step Setup

### 1. Setup Backend Environment
```bash
git clone https://github.com/prem-2323/GEN_AI.git
cd gen-transform-ai

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux / macOS:
source venv/bin/activate

# Install Python backend dependencies
pip install -r Backend/requirements.txt
```

### 2. Setup Frontend Dependencies
```bash
cd Frontend
npm install
cd ..
```

---

## 🔧 Configuration & Environment Variables (`.env`)

Create your `.env` configuration file in the project root:
```bash
cp .env.example .env
```

### Configuration Options Reference

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `ENVIRONMENT` | `development` | Environment mode (`development` or `production`) |
| `PORT` | `8000` | Backend API server listening port |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | Allowed CORS origin for Frontend Vite dev server |
| `STORAGE_ROOT` | `./storage` | Base filesystem path for file uploads and artifacts |
| `MAX_UPLOAD_MB` | `50` | Maximum allowed file upload size in Megabytes |
| `ALLOWED_UPLOAD_EXTS` | `pdf,docx,txt,md,png,jpg,jpeg` | Comma-separated list of allowed document extensions |
| `GRAPH_BACKEND` | `neo4j` | Graph engine (`neo4j` or `mock`) |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j Bolt connection URI |
| `NEO4J_USERNAME` | `neo4j` | Neo4j database username |
| `NEO4J_PASSWORD` | `password` | Neo4j database password |
| `NEO4J_DATABASE` | `neo4j` | Neo4j target database name |
| `VECTOR_BACKEND` | `faiss` | Vector store backend (`faiss` or `memory`) |
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | HuggingFace embedding model ID |
| `EMBEDDING_DIMENSION` | `384` | Embedding vector dimension (384 for bge-small) |
| `EMBEDDING_DEVICE` | `auto` | Device for embeddings (`auto`, `cuda`, or `cpu`) |
| `STUDENT_MODEL_PATH` | `Qwen/Qwen2.5-0.5B-Instruct` | Base model checkpoint ID |
| `STUDENT_ADAPTER_PATH` | `outputs/distillation/student` | Path to fine-tuned QLoRA PEFT adapter weights |

---

## 🖥️ Starting Services (Run Guide)

### Option A: One-Click Startup Script (Recommended)

#### On Windows:
```cmd
start_all.bat
```
*(Automatically launches Neo4j container check, FastAPI Backend on port 8000, and Frontend on port 5173 in separate dedicated terminal windows).*

#### On PowerShell:
```powershell
.\start_all.ps1
```

---

### Option B: Manual Service Startup

#### 1. Start Neo4j Database (Docker or Desktop)
```bash
docker run -d --name doclink-neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest
```

#### 2. Start Backend API Server
```bash
# In first terminal (with venv activated)
python -m uvicorn Backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### 3. Start Frontend Web Application
```bash
# In second terminal
cd Frontend
npm run dev
```

Open your browser at **`http://localhost:5173`** (Frontend UI) and **`http://127.0.0.1:8000/docs`** (Interactive Swagger API documentation).

---

## 📡 REST API Endpoint Catalog

### Ingestion & Documents
- `POST /api/projects/{project_id}/upload` — Upload file to project workspace and trigger Phase 3 extraction pipeline.
- `POST /api/upload` — Standalone document upload and extraction endpoint.
- `GET /api/projects/{project_id}/sources` — List all uploaded sources in a project.
- `GET /api/sources/{source_id}` — Retrieve extracted text, pages, tables, and metadata for a specific source.

### Knowledge Graph (Neo4j)
- `GET /api/graph/health` — Verify Neo4j connectivity, active database, and connection pool status.
- `GET /api/graph/stats` — Return total node counts, edge counts, and graph schema labels.
- `POST /api/graph/query` — Execute parameterized Cypher read queries.
- `GET /api/graph/explore/{node_id}` — Expand $N$-hop neighborhood relationships for visualization.

### Vector Embeddings & Similarity
- `GET /api/embeddings/status` — Return BGE embedding model status, CUDA device, and vector dimensions.
- `POST /api/embeddings/generate` — Generate dense vector representations for input strings.
- `POST /api/embeddings/similarity` — Compute cosine similarity between vectors or text chunks.

### QUBO Evidence Optimization
- `GET /api/qubo/status` — Return QUBO solver configurations and supported algorithms.
- `POST /api/qubo/solve` — Solve a customized quadratic binary matrix optimization problem.

### Grounded RAG & Student LLM
- `GET /api/student/status` — Return QLoRA student LLM device allocation, VRAM usage, and weights status.
- `POST /api/rag/retrieve` — Run dual-channel FAISS + Neo4j retrieval with RRF ranking.
- `POST /api/rag/answer` — Run complete end-to-end grounded RAG pipeline (Retrieve $\to$ RRF $\to$ QUBO $\to$ QLoRA $\to$ Grounding Validation $\to$ Citations).

### Multi-Channel Deliverables & Provenance
- `POST /api/transformation/run` — Generate Executive, Technical, Presentation, and Audio deliverables from UCKR.
- `GET /api/deliverables/{id}/export` — Export deliverable as Markdown (`.md`) or PowerPoint (`.pptx`).
- `GET /api/provenance/records` — Query cryptographic provenance ledger linking claims to source documents.

---

## 🧪 Automated Test Suite & Benchmarks

Run the complete automated test suite covering all phases:

```bash
# Run Grounded RAG, QUBO Optimization, and Ingestion Test Suites
python -m pytest Backend/tests/test_phase3_ingestion_extraction.py Backend/tests/test_phase7_grounded_rag.py Backend/tests/test_qubo_optimization.py Backend/tests/test_hybrid_retrieval.py -v

# Run End-to-End System Performance Benchmark
python Backend/tests/benchmark_phase8.py

# Run System Runtime Verification Suite
python Backend/tests/verify_local_demo_runtime.py
```

---

## 📈 Performance Metrics & Resource Footprint

Empirically measured on standard developer hardware (NVIDIA RTX 3050 Laptop GPU / Intel Core i7 / 16 GB RAM):

| Performance Dimension | Benchmark Measurement |
| :--- | :--- |
| **Peak GPU VRAM Footprint** | **1,125.62 MB** (~1.12 GB VRAM on CUDA) |
| **FAISS Vector Search Latency** | **13 ms – 60 ms** (Sub-100ms response) |
| **QUBO Binary Matrix Optimization** | **3.8 ms – 5.5 ms** (Exact binary solution) |
| **QLoRA Student LLM Inference** | **3.3 s – 9.8 s** (Complete grounded answer generation) |
| **Numerical Grounding Pass Rate** | **100% (5/5 PASS)** (Zero tolerance for unverified numbers) |
| **Full Pipeline Response Time** | **< 10 seconds** (End-to-end question answering) |

---

## 🛡️ Security, Concurrency & Data Integrity

- **Filename Sanitization**: Strip directory traversal components (`../`), shell characters, and path separators from user uploads.
- **Strict Tenant & Project Scoping**: All document lookups verify project ownership and resolve strictly within configured `storage/` boundaries.
- **Thread Safety**: Vector store writes and JSON document repository modifications use reentrant locks (`threading.RLock()`) to guarantee zero race conditions during parallel uploads.
- **Zero Secrets in Source**: No database passwords, API tokens, or credentials are hardcoded. Everything is managed via `.env`.

---

## 📜 License

This project is licensed under the **MIT License** — see the `LICENSE` file for details.
