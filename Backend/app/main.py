"""ContentForge AI Backend — FastAPI + Firebase Auth + Firestore + MongoDB Atlas.

Architecture:
    Frontend (Firebase Auth) -> ID Token -> Verified UID
    -> Users (users/{uid})
    -> Projects (projects/{projectId} where userId == uid)
    -> Sources -> UCKR -> Deliverables

MongoDB:
    30-Minute interval logger into `temp` collection with 24-hr TTL auto-deletion.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config.settings import get_settings
from .config.firebase import init_firebase
from .config.mongo import ensure_core_indexes, get_mongo_db, start_temp_scheduler, stop_temp_scheduler

from .api.routes.health import router as health_router
from .api.routes.auth import router as auth_router
from .api.routes.projects import router as projects_router
from .api.routes.upload import router as upload_router
from .api.routes.sources import router as sources_router
from .api.routes.files import router as files_router
from .api.routes.analysis import router as analysis_router
from .api.routes.pipeline import router as pipeline_router
from .api.routes.transform import router as transform_router
from .api.routes.validation import router as consistency_validation_router
from .api.routes.uckr import router as uckr_full_router, uckr_router, validation_router, temp_router
from .api.routes.direct_text_routes import router as direct_text_router
from .api.routes.export_routes import router as export_routes_router

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("gen-transform")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_firebase()
    try:
        ensure_core_indexes()
    except Exception as exc:
        log.warning("Mongo index setup skipped: %s", exc)
    start_temp_scheduler()
    log.info("%s backend active (env=%s, port=%d)", settings.app_name, settings.environment, settings.port)
    yield
    # Shutdown
    stop_temp_scheduler()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="ContentForge AI backend — Modular, multi-tenant AI transformation platform.",
    lifespan=lifespan,
)

# CORS Configuration
origins = [
    settings.frontend_origin,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
if settings.extra_cors_origins.strip():
    origins += [o.strip() for o in settings.extra_cors_origins.split(",") if o.strip()]
origins = sorted(set(origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(upload_router)
app.include_router(sources_router)
app.include_router(files_router)
app.include_router(analysis_router)
app.include_router(pipeline_router)
app.include_router(transform_router)
app.include_router(uckr_full_router)
app.include_router(uckr_router)
app.include_router(consistency_validation_router)
app.include_router(validation_router)
app.include_router(temp_router)
app.include_router(direct_text_router)
app.include_router(export_routes_router)
