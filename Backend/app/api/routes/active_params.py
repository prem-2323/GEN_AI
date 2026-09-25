"""Phase 11 Active Parameter Mechanism — REST API Router.

Exposes REST endpoints for parameter discovery, active parameter group selection,
dry-run evaluation, and model state restoration.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, Path, status
from typing import Any, Dict

from ...active_params.schemas import (
    ActiveParameterRequest,
    ActiveParameterResponse,
    ParameterInventory,
)
from ...active_params.service import get_active_parameter_service

log = logging.getLogger("gen-transform.api.routes.active_params")

router = APIRouter()


@router.post("/select", response_model=ActiveParameterResponse, summary="Select Active Parameter Groups")
def select_active_parameters(request: ActiveParameterRequest) -> ActiveParameterResponse:
    """Execute active parameter selection policy on a registered PyTorch model."""
    try:
        service = get_active_parameter_service()
        return service.select_parameters(request)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        log.error("Active parameter selection error: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Active parameter selection failed: {exc}")


@router.get("/{model_id}", response_model=ParameterInventory, summary="Get Model Parameter Inventory")
def get_parameter_inventory(
    model_id: str = Path(..., description="Registered PyTorch model identifier")
) -> ParameterInventory:
    """Retrieve parameter groups inventory and memory estimate for a model."""
    try:
        service = get_active_parameter_service()
        return service.get_inventory(model_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        log.error("Failed to fetch parameter inventory for '%s': %s", model_id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch parameter inventory: {exc}")


@router.post("/{model_id}/reset", response_model=ActiveParameterResponse, summary="Reset Model Parameter Activation")
def reset_model_parameters(
    model_id: str = Path(..., description="Registered PyTorch model identifier")
) -> ActiveParameterResponse:
    """Reset model parameters to full activation state."""
    try:
        service = get_active_parameter_service()
        return service.reset_model(model_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        log.error("Failed to reset model parameters for '%s': %s", model_id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to reset model parameters: {exc}")


@router.post("/{model_id}/dry-run", response_model=ActiveParameterResponse, summary="Dry Run Parameter Selection")
def dry_run_parameter_selection(
    model_id: str = Path(..., description="Registered PyTorch model identifier"),
    request_body: Dict[str, Any] = None,
) -> ActiveParameterResponse:
    """Preview active parameter group selection without modifying model parameters state."""
    try:
        service = get_active_parameter_service()
        body = request_body or {}
        req = ActiveParameterRequest(
            model_id=model_id,
            task_type=body.get("task_type"),
            input_metadata=body.get("input_metadata"),
            strategy=body.get("strategy"),
            threshold=body.get("threshold"),
            top_k=body.get("top_k"),
            parameter_budget=body.get("parameter_budget"),
            memory_budget=body.get("memory_budget"),
            dry_run=True,
        )
        return service.select_parameters(req)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        log.error("Dry run active parameter selection failed for '%s': %s", model_id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Dry run selection failed: {exc}")


__all__ = ["router"]
