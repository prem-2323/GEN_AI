"""Phase 9 PyTorch Model Layer API Routes.

Provides REST endpoints for model loading, registry status audits, and inference execution:
- POST /api/models/load
- GET /api/models
- GET /api/models/{model_id}
- POST /api/models/{model_id}/inference
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status

from ...models.config import ModelConfig
from ...models.schemas import (
    ModelInferenceRequest,
    ModelInferenceResponse,
    ModelLoadRequest,
    ModelMetadata,
    ModelStatusResponse,
)
from ...models.service import get_model_service

log = logging.getLogger("gen-transform.api.routes.models")

router = APIRouter(prefix="/api/models", tags=["PyTorch Model Layer"])


@router.get(
    "",
    response_model=List[ModelMetadata],
    status_code=status.HTTP_200_OK,
    summary="List Registered PyTorch Models",
    description="Returns metadata snapshots for all currently registered PyTorch models.",
)
async def list_models() -> List[ModelMetadata]:
    """List registered PyTorch models."""
    try:
        service = get_model_service()
        return service.list_models()
    except Exception as exc:
        log.exception("Error listing registered PyTorch models: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list PyTorch models: {str(exc)}",
        )


@router.post(
    "/load",
    response_model=ModelMetadata,
    status_code=status.HTTP_200_OK,
    summary="Load/Register PyTorch Model",
    description="Loads a PyTorch model into the central ModelRegistry.",
)
async def load_model(req: ModelLoadRequest) -> ModelMetadata:
    """Load and register a PyTorch model."""
    try:
        service = get_model_service()
        cfg = ModelConfig(
            model_id=req.model_id,
            model_name=req.model_name,
            model_type=req.model_type,
            model_path=req.model_path,
            device=req.device,
            dtype=req.dtype,
        )
        return service.load_model(cfg, replace=True)
    except Exception as exc:
        log.exception("Error loading PyTorch model '%s': %s", req.model_id, exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to load PyTorch model: {str(exc)}",
        )


@router.get(
    "/{model_id}",
    response_model=ModelStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get PyTorch Model Status",
    description="Retrieves metadata snapshot and device status for a specific model.",
)
async def get_model_status(model_id: str) -> ModelStatusResponse:
    """Get status of a specific PyTorch model."""
    try:
        service = get_model_service()
        return service.get_model_status(model_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        log.exception("Error retrieving status for model '%s': %s", model_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve model status: {str(exc)}",
        )


@router.post(
    "/{model_id}/inference",
    response_model=ModelInferenceResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute PyTorch Model Inference",
    description="Executes gradient-free inference inside torch.inference_mode().",
)
async def run_model_inference(model_id: str, req: ModelInferenceRequest) -> ModelInferenceResponse:
    """Run model inference for single or batch inputs."""
    if req.model_id != model_id:
        req.model_id = model_id

    try:
        service = get_model_service()
        return service.predict(model_id=model_id, inputs=req.inputs, params=req.params)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        log.exception("Error running inference for model '%s': %s", model_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PyTorch model inference failed: {str(exc)}",
        )
