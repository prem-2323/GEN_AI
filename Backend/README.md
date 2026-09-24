# Gen-Transform-AI — Backend (FastAPI + Firebase Auth + MongoDB)

Architecture:

```text
USER -> Firebase Auth -> UID -> FastAPI (verify token)
    -> MongoDB `contentforge` (what the user owns)
    -> File storage (where the bytes live)
    -> AI models Qwen/Gemma (what the content means)
```

MongoDB `contentforge` collections: `users` `projects` `sources` `uckr`
`deliverables` `validations` `jobs` (+ `temp` 30-min logs, 24h TTL).
Every tenant doc carries `firebaseUid` (+ legacy `userId`); all reads are
owner-scoped. MongoDB stores metadata + results; file bytes live under
`storage/` (Phase 8: Firebase Storage bucket when configured).

## 1. Setup

```powershell
cd Backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# edit .env: set MONGODB_URI (never commit it)
uvicorn app.main:app --reload --port 8000
```

Open: `http://127.0.0.1:8000/docs` (Swagger) · health: `GET /health` and
`GET /api/health` (alias used by the first Postman request).

## 2. Credentials

* MongoDB: `MONGODB_URI` in `.env` (git-ignored). DB name `MONGODB_DB_NAME`
  (default `contentforge`); indexes are created on startup.
* Firebase: optional `serviceAccountKey.json` (git-ignored) for real ID-token
  verification + Firestore mirror. Without it the backend still verifies the
  JWT claims and persists everything to MongoDB.
* AI: optional Ollama daemon (`OLLAMA_BASE_URL`, models `QWEN_MODEL` /
  `GEMMA_MODEL`) and/or `GEMINI_API_KEY`. With neither running, the pipeline
  uses the deterministic extractive fallback (no invented numbers).
* Dev/Postman: `DEV_BYPASS_AUTH=true` accepts `X-User-Uid` headers.
  NEVER enable in production.

## 3. Tests

```powershell
python test_phase2_14.py   # full pipeline: upload -> UCKR -> 7 outputs -> validate -> export -> jobs -> isolation
```

Postman: import `postman_collection.json`. Requests `0-12` cover project CRUD
+ isolation; the **Phase 2-14 pipeline** folder covers upload -> sources ->
analyze -> UCKR -> transform(7) -> validate -> export -> search -> overview ->
background jobs. For `P1` attach any `.pdf/.docx/.txt/.png` as `file`.
Real-token mode: login in the app, `await auth.currentUser.getIdToken()`
in devtools, paste into `idToken`, use `Authorization: Bearer`.

Headers: dev `X-User-Uid: <uid>` (+ optional `X-User-Email`);
real `Authorization: Bearer <Firebase ID token>`.

## 4. Endpoints (all except /health require auth)

| Method | Path | Phase | Notes |
|---|---|---|---|
| GET | `/health`, `/api/health` | — | service + store mode |
| GET | `/api/me` | 1 | upserts `users/{firebaseUid}` (also mirrored) |
| POST/GET | `/api/projects` | 1, 9 | create/list own projects |
| GET/PUT/DELETE | `/api/projects/{id}` | 1 | 403 cross-tenant; delete cascades |
| GET | `/api/projects/{id}/overview` | 9 | project + sources + UCKR + deliverables + validations + jobs |
| POST | `/api/projects/{id}/upload` | 2 | multipart `file`; validates type/size/name; state machine |
| GET | `/api/projects/{id}/sources` | 2 | list own sources |
| GET/DELETE | `/api/sources/{sid}` | 2 | |
| POST | `/api/projects/{id}/analyze` | 3, 4 | `{sourceId}` -> versioned UCKR (+ analysis cache) |
| GET | `/api/projects/{id}/uckr[?sourceId]`, `.../uckr/versions` | 4 | |
| POST | `/api/projects/{id}/transform` | 5 | `{types[], config}` -> 7 deliverables from UCKR |
| GET | `/api/projects/{id}/deliverables` | 5 | |
| POST/GET | `/api/projects/{id}/validate`, `.../validations` | 6 | computed consistency scores |
| POST | `/api/projects/{id}/jobs` | 7 | `{sourceId, outputs?}` background pipeline |
| GET | `/api/jobs/{jid}`, `/api/projects/{id}/jobs` | 7 | poll stage/progress |
| POST | `/api/deliverables/{did}/export?format=md\|json\|pptx` | 10 | writes `storage/outputs/...` |
| GET | `/api/search?q=&kind=all\|project\|source` | 11 | own content only |
| POST | `/api/upload` | legacy | lightweight extraction, no persistence |
| POST | `/api/transform` | legacy | inline text -> outputs (no persistence) |

## 5. Pipeline stage machines

Sources: `uploaded -> validating -> extracting -> completed|failed`.
Jobs: `queued -> extracting -> analyzing_text -> analyzing_images ->
building_uckr -> generating_outputs -> validating -> completed|failed`.

## 6. Security model (Phase 13)

* Firebase token verification (Admin SDK, else claim decode + expiry check).
* Owner scoping on every query (`firebaseUid == uid`); cross-tenant -> 403.
* Upload: extension allowlist, size cap, filename sanitisation, traversal block.
* Secrets only in `.env` (git-ignored); no service-account JSON or API keys in code/frontend.
