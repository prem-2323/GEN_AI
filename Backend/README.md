# Gen-Transform-AI — Architecture & Backend Guide

## Phase 1 — Project Restructuring

The project has completed **Phase 1: Project Restructuring**, establishing modular boundaries, separating HTTP API routing from business logic, and standardizing core infrastructure (configuration, logging, exceptions, schemas) while preserving full compatibility with existing MongoDB, Firebase Auth, and AI processing pipelines.

---

### Current Phase 1 Architecture

```text
React UI
   ↓
FastAPI Layer (main.py)
   ↓
API Routing & Dependencies (api/routes, api/dependencies)
   ↓
Document Ingestion Layer (ingestion/service, ingestion/validator, ingestion/file_manager)
   ↓
Document Extraction Layer (extraction/service - PDF, DOCX, TXT, MD, Images)
   ↓
Core Engines & Database Adapters (core/, services/, config/mongo, services/storage)
```

---

### Future Planned System Architecture (Phases 2 – 16)

```text
React UI
   ↓
FastAPI Entrypoint
   ↓
Document Ingestion (Phase 3)
   ↓
Document Extraction (Phase 3)
   ↓
DocLink Entity / Fact / Relation Engine (Phase 4)
   ↓
Neo4j Knowledge Graph + Vector Index (Phase 5)
   ↓
Hybrid Vector + Graph RAG (Phase 7)
   ↓
Quantum / Hybrid Optimization (Phase 8)
   ↓
PyTorch Model Layer (Phase 9)
   ↓
Knowledge Distillation (Phase 10)
   ↓
Active Parameter Engine (Phase 11)
   ↓
Transformation Engine (Phase 12)
   ↓
Validation + Consistency Engine (Phase 13)
   ↓
Provenance / Evidence Lineage (Phase 14)
   ↓
React Output UI (Phase 15)
```

> **Note on Future Phases**: Module boundaries (`doclink/`, `graph/`, `embeddings/`, `rag/`, `optimization/`, `distillation/`, `active_params/`, `provenance/`) are provisioned as architectural boundaries. Full algorithm implementations and database migrations (e.g., removing Firebase/MongoDB in favor of Neo4j) are scheduled for their respective future phases.

---

## Backend Directory Structure

```text
Backend/
├── main.py                     # Root FastAPI entrypoint shim
├── app/
│   ├── main.py                 # Core FastAPI application with routers & middleware
│   ├── auth.py                 # Backward-compatible auth shim
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py     # Auth & context dependencies
│   │   └── routes/             # Clean HTTP route handlers
│   │       ├── health.py
│   │       ├── auth.py
│   │       ├── projects.py
│   │       ├── upload.py
│   │       ├── sources.py
│   │       ├── files.py
│   │       ├── analysis.py
│   │       ├── pipeline.py
│   │       ├── transform.py
│   │       ├── validation.py
│   │       ├── uckr.py
│   │       ├── direct_text_routes.py
│   │       └── export_routes.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Centralized Pydantic settings & env management
│   │   ├── constants.py        # Application constants & mime mappings
│   │   ├── exceptions.py       # Centralized exception hierarchy
│   │   ├── logging.py          # Structured logger configuration
│   │   └── schemas.py          # Universal Pydantic schemas
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── service.py          # Ingestion orchestration
│   │   ├── validator.py        # File validation & sanitization
│   │   └── file_manager.py     # Disk & GridFS file storage
│   ├── extraction/
│   │   ├── __init__.py
│   │   └── service.py          # PDF / DOCX / TXT / Image extraction
│   ├── doclink/                # Boundary for DocLink engine (Phase 4)
│   ├── graph/                  # Boundary for Neo4j Knowledge Graph (Phase 5)
│   ├── embeddings/             # Boundary for Semantic Chunking & Vectors (Phase 6)
│   ├── rag/                    # Boundary for Hybrid Vector + Graph RAG (Phase 7)
│   ├── optimization/           # Boundary for Quantum/Hybrid Optimization (Phase 8)
│   ├── models/                 # Domain schemas & PyTorch model boundary (Phase 9)
│   ├── distillation/           # Boundary for Knowledge Distillation (Phase 10)
│   ├── active_params/          # Boundary for Active Parameter Engine (Phase 11)
│   ├── transformation/         # Boundary & wrapper for Transformation Engine
│   ├── validation/             # Boundary & wrapper for Consistency Validation
│   ├── provenance/             # Boundary for Evidence Lineage (Phase 14)
│   ├── config/                 # Database configuration (MongoDB Atlas, Firebase)
│   ├── services/               # Internal business domain services
│   └── utils/                  # Helper utilities
├── tests/                      # Automated test suites
├── requirements.txt
└── .env.example
```

---

## Running Locally

```powershell
# Start Backend
cd Backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start Full Platform (Backend + Frontend)
cd ..
.\start.bat
```

- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`
- Frontend: `http://localhost:3000`
