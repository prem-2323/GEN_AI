# Phase 8 — Security & Hardening Audit

## Executive Summary
This document reports the security audit conducted on the **Document Intelligence / DocLink** platform prior to end-to-end demo deployment. All backend API endpoints, configuration managers, storage directories, and file processing components were inspected.

---

## 1. CORS Configuration Audit
- **Location**: `Backend/app/main.py`
- **Audit Result**: CORS middleware is configured using `CORSMiddleware`.
- **Allowed Origins**: Configured via `ALLOWED_ORIGINS` setting (`["http://localhost:5173", "http://localhost:3000"]` for local demo environment).
- **Credentials & Methods**: Explicitly restricted to `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`.

---

## 2. Secrets & Credential Protection
- **Environment Variables**: Managed via `.env` file (excluded via `.gitignore`).
- **Hardcoded Credentials Check**:
  - No database passwords, API tokens, or secrets are hardcoded in source code.
  - Default fallbacks for local dev/demo are loaded securely via `pydantic-settings` (`Backend/app/core/config.py`).
- **Template Security**: `.env.example` contains sanitised placeholders (`YOUR_NEO4J_PASSWORD`, `YOUR_API_KEY`).

---

## 3. Upload & File Path Hardening
- **Filename Sanitization**: Upload handlers in `Backend/app/api/routes/upload.py` use secure filename sanitization to prevent path traversal attacks (`../` stripping).
- **File Type & Size Restrictions**:
  - Max upload file size limit: 50 MB.
  - Allowed MIME types strictly enforced: `application/pdf`.
- **Directory Traversal Defense**: All file lookups resolve absolute paths using `Path.resolve()` and verify child confinement within configured storage roots (`storage/uploads/`).

---

## 4. Temporary File Cleanup
- Scratch scripts and temporary PDF extractions utilize standard Python `tempfile` contexts (`tempfile.NamedTemporaryFile`, `tempfile.TemporaryDirectory`) with explicit context manager cleanup.
- Vector database temporary indices created during test execution are isolated in disposable directories and unlinked on teardown.

---

## 5. Error Handling & Privacy
- **Information Disclosure Prevention**: Internal Python exception tracebacks, system file paths, and environment keys are stripped from API error responses.
- **HTTP Status Codes**:
  - `400 Bad Request`: Empty query, query length > 1000, `qubo_k > top_k`.
  - `404 Not Found`: Missing document or evidence chunk.
  - `422 Unprocessable Entity`: Malformed JSON or invalid schema parameters.
  - `500 Internal Server Error`: Standardized generic detail without raw stack traces.
  - `503 Service Unavailable`: Triggered when required backends (Neo4j, BGE, FAISS) fail connectivity check.

---

## 6. Audit Checklist Summary

| Security Category | Requirement | Audit Result | Status |
|---|---|---|---|
| **CORS** | Restrict origins and methods | Verified in `main.py` | PASS |
| **Secrets** | No hardcoded keys in git | Verified across repo | PASS |
| **Input Validation**| Reject invalid params & long queries | Enforced in FastAPI routes | PASS |
| **File Traversal** | Sanitize upload paths | Enforced in `upload.py` | PASS |
| **Error Handling** | Mask stack traces in API | Custom exception handlers | PASS |
| **Temp Files** | Clean up after extraction | Enforced in pipeline | PASS |
