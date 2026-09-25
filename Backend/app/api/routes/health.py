"""Health and root routes."""
from __future__ import annotations

from fastapi import APIRouter
from ...config.settings import get_settings

router = APIRouter(tags=["health"])


@router.get("/")
async def root():
    settings = get_settings()
    return {
        "name": settings.app_name,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


@router.get("/health")
@router.get("/api/health", include_in_schema=False)
async def health():
    settings = get_settings()
    return {
        "ok": True,
        "status": "healthy",
        "name": settings.app_name,
        "environment": settings.environment,
    }

