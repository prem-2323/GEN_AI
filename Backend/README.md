# Gen-Transform-AI — Architecture & Backend Guide

## Phase 1 — Project Restructuring

The project uses a local JSON document repository and filesystem storage, with modular FastAPI routes and AI processing pipelines. The application has no account authentication or cloud database integration.

---

### Current Phase 1 Architecture

```text
React UI (Port 3000)
   ↓
Canonical FastAPI Entrypoint (app/main.py — Port 8000)
   ↓
API Routing & Dependencies (app/api/routes, app/api/dependencies)
   ↓
Document Ingestion Layer (app/ingestion/service, validator, file_manager)
   ↓
Document Extraction Layer (app/extraction/service - PDF, DOCX, TXT, MD, Images)
   ↓
Domain Schemas & Services (app/domain_models/, app/core/, app/services/)
   ↓
Local Persistence Layer (JSON document repository and filesystem storage)
```

---

### Canonical Entry Point

The single canonical backend entry point is:

```powershell
# From the Backend directory:
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### Future Planned System Architecture (Phases 2 – 16)

```text
React UI
   ↓
FastAPI Entrypoint (app.main:app)
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
PyTorch Model Layer (Phase 9 — app/models/)
   ↓
Knowledge Distillation (Phase 10 — app/distillation/)
   ↓
Active Parameter Engine (Phase 11 — app/active_params/)
   ↓
Transformation Engine (Phase 12 — app/transformation/)
   ↓
Validation + Consistency Engine (Phase 13 — app/validation/)
   ↓
Provenance / Evidence Lineage (Phase 14 — app/provenance/)
   ↓
React Output UI (Phase 15)
```

---

## Backend Directory Structure

```text
Backend/
├── app/
│   ├── main.py                 # Canonical FastAPI application
│   ├── auth.py                 # Local workspace identity shim
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py     # Anonymous workspace context
│   │   └── routes/             # Clean HTTP route handlers
│   │       ├── health.py
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
│   │   └── file_manager.py     # Local disk file storage
│   ├── extraction/
│   │   ├── __init__.py
│   │   └── service.py          # PDF / DOCX / TXT / Image extraction
│   ├── domain_models/          # Application & database domain schemas (UCKR, Projects, Deliverables)
│   ├── models/                 # PyTorch / AI Model Layer boundary (Phase 9)
│   ├── doclink/                # Boundary for DocLink engine (Phase 4)
│   ├── graph/                  # Boundary for Neo4j Knowledge Graph (Phase 5)
│   ├── embeddings/             # Boundary for Semantic Chunking & Vectors (Phase 6)
│   ├── rag/                    # Boundary for Hybrid Vector + Graph RAG (Phase 7)
│   ├── optimization/           # Boundary for Quantum/Hybrid Optimization (Phase 8)
│   ├── distillation/           # Boundary for Knowledge Distillation (Phase 10)
│   ├── active_params/          # Boundary for Active Parameter Engine (Phase 11)
│   ├── transformation/         # Boundary & wrapper for Transformation Engine
│   ├── validation/             # Boundary & wrapper for Consistency Validation
│   ├── provenance/             # Boundary for Evidence Lineage (Phase 14)
│   ├── config/                 # Application settings
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
