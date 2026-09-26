"""Phase 7 Student Model API Routes.

Provides:
- GET /api/student/status — Operational availability of QLoRA student model.
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from ...services.student_service import get_student_service

log = logging.getLogger("gen-transform.api.routes.student")

router = APIRouter(prefix="/api/student", tags=["QLoRA Student Model"])


class StudentStatusResponse(BaseModel):
    """Response payload for GET /api/student/status."""
    available: bool
    base_model: str
    adapter: str
    adapter_exists: bool
    adapter_loaded: bool
    device: str
    cuda_available: bool


@router.get(
    "/status",
    response_model=StudentStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get QLoRA Student Model Operational Status",
)
async def get_student_status() -> StudentStatusResponse:
    """Return availability and configuration of fine-tuned student model."""
    service = get_student_service()
    status_data = service.get_status()
    return StudentStatusResponse(**status_data)
