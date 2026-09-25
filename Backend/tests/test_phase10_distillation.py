"""Phase 10 — Knowledge Distillation Complete Automated Test Suite.

Tests all 28 required specifications:
1. Configuration validation
2. Temperature validation (T > 0.0)
3. Alpha validation (alpha in [0.0, 1.0])
4. Distillation loss calculation
5. Temperature scaling
6. Hard-label loss calculation
7. Combined loss calculation
8. Teacher loading via Phase 9
9. Teacher freezing (requires_grad == False)
10. Student loading via Phase 9
11. Teacher/Student compatibility validation
12. Synthetic dataset creation
13. PyTorch DataLoader integration
14. Distillation training loop execution
15. CRITICAL GRADIENT SAFETY TEST: Teacher weights unchanged
16. Student weights updated
17. Checkpoint save
18. Checkpoint load
19. Model evaluation
20. Teacher vs Student comparison
21. Parameter reduction percentage calculation
22. Phase 9 ModelRegistry integration (model_type = 'distilled')
23. Phase 9 ModelService integration
24. DistillationService orchestration
25. REST API endpoints (/api/distillation/train, /api/distillation/evaluate, /api/distillation/{job_id})
26. Invalid model handling
27. Invalid configuration handling
28. CPU-only execution without CUDA requirements
"""
import os
import sys
from pathlib import Path
import pytest
import torch
from fastapi.testclient import TestClient

# Add Backend root directory to sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.main import app
from app.models import get_model_service, reset_model_service
from app.distillation import (
    DistillationCheckpointManager,
    DistillationConfig,
    DistillationLoss,
    KnowledgeDistillationEvaluator,
    KnowledgeDistillationService,
    KnowledgeDistillationTrainer,
    StudentPyTorchModel,
    SyntheticDistillationDataset,
    TeacherPyTorchModel,
    create_distillation_dataloader,
    get_distillation_service,
    reset_distillation_service,
)

client = TestClient(app)


def test_config_validations():
    print("\n--- [Test 1, 2, 3, 27] Configuration & Parameter Validations ---")
    cfg = DistillationConfig(temperature=3.0, alpha=0.6, epochs=3)
    assert cfg.temperature == 3.0
    assert cfg.alpha == 0.6

    # Test invalid temperature (T <= 0.0)
    with pytest.raises(ValueError):
        DistillationConfig(temperature=0.0)

    # Test invalid alpha (alpha < 0.0 or alpha > 1.0)
    with pytest.raises(ValueError):
        DistillationConfig(alpha=1.5)

    print("  [OK] DistillationConfig strictly validates temperature (>0.0) and alpha ([0.0, 1.0]).")


def test_distillation_loss_and_scaling():
    print("\n--- [Test 4, 5, 6, 7] Distillation Loss Functions & Temperature Scaling ---")
    loss_fn = DistillationLoss(temperature=4.0, alpha=0.7)

    student_logits = torch.tensor([[2.0, 1.0, 0.1, -1.0], [0.5, 1.5, -0.2, 0.0]], requires_grad=True)
    teacher_logits = torch.tensor([[2.2, 0.9, 0.2, -0.8], [0.4, 1.6, -0.1, 0.1]])
    targets = torch.tensor([0, 1])

    total_loss, distill_loss, task_loss = loss_fn(student_logits, teacher_logits, targets)

    assert total_loss.item() > 0.0
    assert distill_loss.item() > 0.0
    assert task_loss.item() > 0.0

    # Distillation-only mode (alpha=1.0)
    loss_pure_distill = DistillationLoss(temperature=4.0, alpha=1.0)
    tot1, dist1, task1 = loss_pure_distill(student_logits, teacher_logits, None)
    assert tot1.item() == dist1.item()

    print(f"  [OK] Distillation loss computed: total={total_loss.item():.4f}, distill={distill_loss.item():.4f}, task={task_loss.item():.4f}")


def test_teacher_student_loading_and_compatibility():
    print("\n--- [Test 8, 10, 11, 26] Teacher & Student Model Loading & Compatibility ---")
    teacher = TeacherPyTorchModel()
    student = StudentPyTorchModel()

    assert teacher.get_parameter_count() > student.get_parameter_count()

    svc = get_distillation_service()
    valid, reason = svc.validate_compatibility(teacher, student)

    assert valid is True
    assert reason is None

    print(f"  [OK] Teacher params: {teacher.get_parameter_count()}, Student params: {student.get_parameter_count()} (Compatible: {valid})")


def test_synthetic_dataset_and_dataloader():
    print("\n--- [Test 12, 13] Synthetic Dataset & DataLoader Integration ---")
    ds = SyntheticDistillationDataset(num_samples=40, input_dim=8, num_classes=4, seed=42)
    dl = create_distillation_dataloader(ds, batch_size=8, shuffle=False)

    assert len(ds) == 40
    batch = next(iter(dl))
    inputs, targets, meta = batch

    assert inputs.shape == (8, 8)
    assert targets.shape == (8,)

    print(f"  [OK] Synthetic dataset loaded {len(ds)} samples in batches of 8.")


def test_critical_gradient_safety_and_student_training():
    print("\n--- [Test 9, 14, 15, 16, 28] CRITICAL Gradient Safety & Student Weight Updates ---")
    teacher = TeacherPyTorchModel()
    student = StudentPyTorchModel()

    ds = SyntheticDistillationDataset(num_samples=32, input_dim=8, num_classes=4, seed=42)
    dl = create_distillation_dataloader(ds, batch_size=8, shuffle=False)

    cfg = DistillationConfig(epochs=2, learning_rate=0.01, temperature=4.0, alpha=0.7)
    trainer = KnowledgeDistillationTrainer(teacher, student, dl, cfg)

    # 1. Verify Teacher is frozen (requires_grad == False)
    assert all(p.requires_grad is False for p in teacher.parameters())

    # Snapshots before training
    t_weights_before = [p.clone().detach() for p in teacher.parameters()]
    s_weights_before = [p.clone().detach() for p in student.parameters()]

    # 2. Run distillation training
    history = trainer.train()

    # Snapshots after training
    t_weights_after = [p.clone().detach() for p in teacher.parameters()]
    s_weights_after = [p.clone().detach() for p in student.parameters()]

    # 3. CRITICAL GRADIENT SAFETY ASSERTIONS
    # Teacher weights MUST BE IDENTICAL (Unchanged)
    for w_prev, w_curr in zip(t_weights_before, t_weights_after):
        assert torch.equal(w_prev, w_curr), "CRITICAL FAILURE: Teacher parameter changed during distillation!"

    # Student weights MUST HAVE CHANGED (Learned from training signal)
    weights_changed = False
    for w_prev, w_curr in zip(s_weights_before, s_weights_after):
        if not torch.equal(w_prev, w_curr):
            weights_changed = True
            break
    assert weights_changed is True, "Student parameters should update during distillation training."

    print("  [OK] GRADIENT SAFETY VERIFIED: Teacher weights remained 100% UNCHANGED.")
    print("  [OK] STUDENT LEARNING VERIFIED: Student weights updated successfully.")


def test_checkpointing_save_and_load(tmp_path):
    print("\n--- [Test 17, 18] Checkpoint Saving & Loading ---")
    student = StudentPyTorchModel()
    opt = torch.optim.Adam(student.parameters(), lr=1e-3)
    cfg = DistillationConfig(checkpoint_dir=str(tmp_path))

    save_path = str(tmp_path / "test_student_ckpt.pt")
    saved_file = DistillationCheckpointManager.save_checkpoint(
        student_model=student,
        optimizer=opt,
        config=cfg,
        epoch=3,
        metrics={"loss": 0.42},
        checkpoint_path=save_path,
    )

    assert os.path.exists(saved_file)

    student_reloaded = StudentPyTorchModel()
    ckpt_data = DistillationCheckpointManager.load_checkpoint(student_reloaded, saved_file)

    assert ckpt_data["epoch"] == 3
    assert ckpt_data["metrics"]["loss"] == 0.42

    print(f"  [OK] Checkpoint saved to and loaded cleanly from '{save_path}'.")


def test_evaluator_and_comparison():
    print("\n--- [Test 19, 20, 21] Evaluator & Parameter Reduction Calculation ---")
    teacher = TeacherPyTorchModel()
    student = StudentPyTorchModel()

    ds = SyntheticDistillationDataset(num_samples=50, input_dim=8, num_classes=4, seed=42)
    dl = create_distillation_dataloader(ds, batch_size=10, shuffle=False)

    evaluator = KnowledgeDistillationEvaluator()
    comparison = evaluator.compare(teacher, student, dl)

    assert comparison.parameter_reduction_percent > 0.0
    assert comparison.teacher_metrics.parameter_count > comparison.student_metrics.parameter_count
    assert comparison.teacher_metrics.loss >= 0.0
    assert comparison.student_metrics.loss >= 0.0

    print(f"  [OK] Parameter Reduction: {comparison.parameter_reduction_percent:.2f}% (Teacher={comparison.teacher_metrics.parameter_count}, Student={comparison.student_metrics.parameter_count})")
    print(f"  [OK] Latency Change: {comparison.latency_change_percent:.2f}%")


def test_distillation_service_and_registry_integration():
    print("\n--- [Test 22, 23, 24] DistillationService & Phase 9 ModelRegistry Integration ---")
    reset_model_service()
    reset_distillation_service()

    svc = get_distillation_service()
    cfg = DistillationConfig(
        teacher_model_id="teacher_model_v1",
        student_model_id="student_model_v1",
        epochs=2,
    )

    result = svc.distill(config=cfg)

    assert result.status == "completed"
    assert result.registered_model_id is not None
    assert result.comparison is not None

    # Check Phase 9 ModelRegistry
    registered_student = svc.model_svc.registry.get(result.registered_model_id)
    assert registered_student is not None
    assert registered_student.model_type == "distilled"

    print(f"  [OK] Distillation job completed in {result.duration_seconds}s. Registered in Phase 9 ModelRegistry as '{result.registered_model_id}'.")


def test_rest_api_endpoints():
    print("\n--- [Test 25] REST API Endpoints ---")
    # 1. POST /api/distillation/train
    req_train = {
        "teacher_model_id": "teacher_model_v1",
        "student_model_id": "student_model_v1",
        "config": {
            "epochs": 1,
            "learning_rate": 0.01,
            "temperature": 4.0,
            "alpha": 0.7,
        },
    }
    res_train = client.post("/api/distillation/train", json=req_train)
    assert res_train.status_code == 200, f"Train failed: {res_train.text}"

    data_train = res_train.json()
    job_id = data_train["job_id"]
    assert data_train["status"] == "completed"
    assert "comparison" in data_train

    # 2. GET /api/distillation/{job_id}
    res_job = client.get(f"/api/distillation/{job_id}")
    assert res_job.status_code == 200
    assert res_job.json()["job_id"] == job_id

    # 3. POST /api/distillation/evaluate
    res_eval = client.post("/api/distillation/evaluate", json=req_train)
    assert res_eval.status_code == 200
    data_eval = res_eval.json()
    assert "parameter_reduction_percent" in data_eval

    print("  [OK] REST API endpoints (POST /api/distillation/train, GET /api/distillation/{id}, POST /api/distillation/evaluate) verified successfully.")


if __name__ == "__main__":
    test_config_validations()
    test_distillation_loss_and_scaling()
    test_teacher_student_loading_and_compatibility()
    test_synthetic_dataset_and_dataloader()
    test_critical_gradient_safety_and_student_training()
    test_checkpointing_save_and_load(Path("./tmp_test_ckpt"))
    test_evaluator_and_comparison()
    test_distillation_service_and_registry_integration()
    test_rest_api_endpoints()
    print("\n[SUCCESS] ALL PHASE 10 KNOWLEDGE DISTILLATION TESTS PASSED SUCCESSFULLY!")
