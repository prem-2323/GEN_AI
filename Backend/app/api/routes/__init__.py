"""API Routes package."""
from .health import router as health_router
from .auth import router as auth_router
from .projects import router as projects_router
from .sources import router as sources_router
from .analysis import router as analysis_router
from .upload import router as upload_router
from .transform import router as transform_router
from .uckr import uckr_router, validation_router, temp_router

__all__ = [
    "health_router",
    "auth_router",
    "projects_router",
    "sources_router",
    "analysis_router",
    "upload_router",
    "transform_router",
    "uckr_router",
    "validation_router",
    "temp_router",
]
