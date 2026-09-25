# Gen-Transform-AI — Enterprise Document Transformation Platform

## Architecture Overview (Phase 1 Restructuring Completed)

Gen-Transform-AI transforms raw documents (PDF, DOCX, TXT, Images) into verified, lineage-backed executive deliverables (Executive Summaries, Strategic Advisories, Slide Decks, and Audio Briefings).

### Current Phase 1 Request Flow

```text
React UI (Port 3000)
       ↓
FastAPI Backend (Port 8000)
       ↓
API Layer (app/api/)
       ↓
Document Ingestion Layer (app/ingestion/)
       ↓
Document Extraction Layer (app/extraction/)
       ↓
Core Domain Engines & Storage (app/services/, MongoDB GridFS)
```

### Full Target Architecture (Phases 1 – 16)

```text
React UI
   ↓
FastAPI
   ↓
Document Ingestion
   ↓
Document Extraction
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
Validation + Consistency (Phase 13)
   ↓
Provenance / Evidence Tracking (Phase 14)
   ↓
React Output UI (Phase 15)
```

---

## Quick Start

1. Start both Frontend and Backend concurrently using the launcher:
   ```cmd
   .\start.bat
   ```
2. Or start services manually:
   - Backend: `cd Backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
   - Frontend: `cd Frontend && npm run dev`
