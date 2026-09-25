"""Phase 10 Knowledge Distillation API Routes.

Provides REST endpoints for Knowledge Distillation training, evaluation, and checkpoint management:
- POST /api/distillation/train
- POST /api/distillation/evaluate
- GET /api/distillation/{job_id}
- POST /api/distillation/checkpoint
"""
from __future__ import annotations

import logging
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status

from ...distillation.config import DistillationConfig, PaperDistillationConfig
from ...distillation.dataset_generator import create_dataset
from ...distillation.pipeline import run_paper_test
from ...distillation.train import inspect_runtime, run_qlora_training
from ...distillation.schemas import (
    DistillationComparison,
    DistillationRequest,
    DistillationResult,
    DistillationStatusResponse,
)
from ...distillation.service import get_distillation_service

log = logging.getLogger("gen-transform.api.routes.distillation")

router = APIRouter(prefix="/api/distillation", tags=["Knowledge Distillation"])

# In-memory store for tracking distillation job results
_DISTILLATION_JOBS: Dict[str, DistillationResult] = {}
_PAPER_DISTILLATION_RUNS: Dict[str, Dict[str, Any]] = {}


@router.post(
    "/train",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Execute Knowledge Distillation Training",
    description="Trains a Student PyTorch Model using temperature-scaled soft targets from a Teacher PyTorch Model.",
)
async def train_distillation(req: DistillationRequest) -> DistillationResult:
    """Execute knowledge distillation run."""
    try:
        if req.project_id and req.source_id:
            run_id = f"paper_{req.project_id}_{req.source_id}"
            training = run_qlora_training(PaperDistillationConfig())
            result = {"run_id": run_id, "status": training.get("status"), "training": training}
            _PAPER_DISTILLATION_RUNS[run_id] = result
            return result
        service = get_distillation_service()
        cfg = req.config or DistillationConfig(
            teacher_model_id=req.teacher_model_id,
            student_model_id=req.student_model_id,
        )
        result = service.distill(config=cfg)
        _DISTILLATION_JOBS[result.job_id] = result
        return result
    except Exception as exc:
        log.exception("Error executing distillation training: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Knowledge distillation training failed: {str(exc)}",
        )


@router.post(
    "/evaluate",
    response_model=DistillationComparison,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Teacher vs Student Performance",
    description="Compares loss, accuracy, inference latency, and parameter counts between Teacher and Student models.",
)
async def evaluate_distillation(req: DistillationRequest) -> DistillationComparison:
    """Evaluate teacher vs student performance."""
    try:
        if req.project_id and req.source_id:
            run_id = f"paper_{req.project_id}_{req.source_id}"
            return _PAPER_DISTILLATION_RUNS.get(run_id, {"run_id": run_id, "status": "not_started", "message": "Run /test first."})
        service = get_distillation_service()
        teacher = service.model_svc.registry.get(req.teacher_model_id)
        student = service.model_svc.registry.get(req.student_model_id)

        if not teacher or not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Teacher or Student model not found in registry (Teacher: '{req.teacher_model_id}', Student: '{req.student_model_id}').",
            )

        from ...distillation.data import SyntheticDistillationDataset, create_distillation_dataloader
        ds = SyntheticDistillationDataset(num_samples=100, input_dim=8, num_classes=4, seed=42)
        dl = create_distillation_dataloader(ds, batch_size=16, shuffle=False)

        comparison = service.evaluator.compare(teacher=teacher, student=student, dataloader=dl)
        return comparison
    except HTTPException:
        raise
    except Exception as exc:
        log.exception("Error evaluating distillation: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Distillation evaluation failed: {str(exc)}",
        )


@router.post("/create-dataset")
async def create_paper_dataset(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create grounded train/validation/test JSONL files from an existing source."""
    project_id = payload.get("project_id") or payload.get("projectId")
    source_id = payload.get("source_id") or payload.get("sourceId")
    if not project_id or not source_id:
        raise HTTPException(status_code=422, detail="project_id and source_id are required.")
    cfg = PaperDistillationConfig(**{k: v for k, v in payload.items() if k in PaperDistillationConfig.model_fields})
    result = create_dataset(project_id, source_id, cfg)
    run_id = f"paper_{project_id}_{source_id}"
    _PAPER_DISTILLATION_RUNS[run_id] = {"run_id": run_id, **result}
    return _PAPER_DISTILLATION_RUNS[run_id]


@router.post("/test")
async def test_paper_distillation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Run dataset creation, teacher validation, training gate, and comparison."""
    project_id = payload.get("project_id") or payload.get("projectId")
    source_id = payload.get("source_id") or payload.get("sourceId")
    if not project_id or not source_id:
        raise HTTPException(status_code=422, detail="project_id and source_id are required.")
    result = run_paper_test(project_id, source_id)
    run_id = f"paper_{project_id}_{source_id}"
    _PAPER_DISTILLATION_RUNS[run_id] = {"run_id": run_id, **result}
    return _PAPER_DISTILLATION_RUNS[run_id]


@router.get("/status")
async def paper_distillation_status() -> Dict[str, Any]:
    return {"runtime": inspect_runtime(), "runs": list(_PAPER_DISTILLATION_RUNS.values())}


@router.get(
    "/{job_id}",
    response_model=DistillationStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Distillation Job Status",
    description="Retrieves the status and metrics result for a specific distillation job.",
)
async def get_distillation_job(job_id: str) -> DistillationStatusResponse:
    """Get status of a distillation job."""
    if job_id not in _DISTILLATION_JOBS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Distillation job '{job_id}' not found.",
        )

    result = _DISTILLATION_JOBS[job_id]
    return DistillationStatusResponse(
        job_id=job_id,
        status=result.status,
        progress=1.0 if result.status == "completed" else 0.0,
        result=result,
    )
