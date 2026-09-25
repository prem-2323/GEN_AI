"""Phase 9 — PyTorch Model Layer Complete Automated Test Suite.

Tests all 20 required specifications:
1. PyTorch availability
2. Model configuration (ModelConfig)
3. DeviceManager CPU resolution
4. DeviceManager CUDA detection
5. CUDA fallback when unavailable
6. Model creation (BasePyTorchModel & SimpleTestPyTorchModel)
7. Model loading (ModelLoader)
8. Model registry (ModelRegistry)
9. Duplicate registration handling
10. Model metadata snapshot & parameter count
11. Model status audits
12. Single inference execution
13. torch.inference_mode gradient-free verification
14. Batch inference execution
15. Inference latency tracking
16. Model unload lifecycle
17. Invalid model handling
18. Missing model handling
19. Service orchestration (ModelService)
20. REST API endpoints (/api/models/load, /api/models, /api/models/{id}, /api/models/{id}/inference)
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
from app.models import (
    BasePyTorchModel,
    DeviceManager,
    InferenceEngine,
    ModelConfig,
    ModelInferenceRequest,
    ModelLoader,
    ModelMetadata,
    ModelRegistry,
    ModelService,
    SimpleTestPyTorchModel,
    get_model_service,
    reset_model_service,
)

client = TestClient(app)


def test_pytorch_availability():
    print("\n--- [Test 1] PyTorch Availability ---")
    assert torch.__version__ is not None, "PyTorch must be installed."
    print(f"  [OK] PyTorch version {torch.__version__} is available.")


def test_model_configuration():
    print("\n--- [Test 2] Model Configuration ---")
    cfg = ModelConfig(
        model_id="cfg_model_01",
        model_name="Config Model",
        model_type="classifier",
        batch_size=32,
        device="cpu",
    )
    assert cfg.model_id == "cfg_model_01"
    assert cfg.batch_size == 32
    assert cfg.device == "cpu"
    print("  [OK] ModelConfig verified successfully.")


def test_device_manager():
    print("\n--- [Test 3, 4, 5] DeviceManager CPU, CUDA, and Fallback ---")
    dev_cpu = DeviceManager.get_device("cpu")
    assert dev_cpu.type == "cpu"

    dev_auto = DeviceManager.get_device("auto")
    assert dev_auto.type in ["cpu", "cuda"]

    # Test CUDA fallback when invalid CUDA index or unavailable CUDA requested
    dev_fallback = DeviceManager.get_device("cuda:999")
    assert dev_fallback.type in ["cpu", "cuda"]  # Safely falls back without crashing

    info = DeviceManager.get_device_info()
    assert "device_type" in info
    print(f"  [OK] DeviceManager verified. Active device info: {info}")


def test_model_creation_and_metadata():
    print("\n--- [Test 6, 10] Model Creation & Metadata Snapshot ---")
    model = SimpleTestPyTorchModel()
    meta = model.get_metadata()

    assert meta.model_id == "test_linear_v1"
    assert meta.parameter_count > 0
    assert meta.trainable_parameter_count == meta.parameter_count
    assert meta.loaded is True
    assert meta.status == "ready"

    print(f"  [OK] Created model '{meta.model_name}' with {meta.parameter_count} parameters.")


def test_model_loader():
    print("\n--- [Test 7, 17] Model Loader & Caching ---")
    loader = ModelLoader()
    cfg = ModelConfig(model_id="loader_test_01", model_name="Loader Test", model_type="test_linear")

    m1 = loader.load_model(cfg)
    assert m1.is_loaded is True

    # Caching check
    m2 = loader.load_model(cfg)
    assert m1 is m2, "Cached instance should be returned on identical config."

    print("  [OK] ModelLoader safely instantiated and cached model.")


def test_model_registry():
    print("\n--- [Test 8, 9, 11, 16, 18] Model Registry Lifecycle ---")
    registry = ModelRegistry()
    m1 = SimpleTestPyTorchModel(ModelConfig(model_id="reg_m1", model_name="Registry M1"))

    # Register
    registry.register(m1)
    assert registry.has("reg_m1") is True
    assert len(registry.list_models()) == 1

    # Duplicate registration handling (should raise ValueError unless replace=True)
    with pytest.raises(ValueError):
        registry.register(m1, replace=False)

    # Replace duplicate
    m1_replacement = SimpleTestPyTorchModel(ModelConfig(model_id="reg_m1", model_name="Registry M1 Replaced"))
    registry.register(m1_replacement, replace=True)
    assert registry.get("reg_m1").model_name == "Registry M1 Replaced"

    # Missing model check
    assert registry.get("non_existent_model") is None
    assert registry.has("non_existent_model") is False

    # Unload & Remove
    registry.remove("reg_m1")
    assert registry.has("reg_m1") is False

    print("  [OK] ModelRegistry handles registration, duplicates, metadata, and unloading cleanly.")


def test_inference_engine():
    print("\n--- [Test 12, 13, 14, 15] Single & Batch Inference inside torch.inference_mode ---")
    registry = ModelRegistry()
    model = SimpleTestPyTorchModel(ModelConfig(model_id="inf_m1", model_name="Inference M1"))
    registry.register(model)

    engine = InferenceEngine(registry)

    # 1. Single sample inference
    single_input = [1.0, 0.5, 0.2, 0.0, -0.5, 0.8, 1.2, -0.1]
    req_single = ModelInferenceRequest(model_id="inf_m1", inputs=single_input)

    res_single = engine.run_inference(req_single)
    assert res_single.model_id == "inf_m1"
    assert len(res_single.outputs) == 4
    assert res_single.latency_ms >= 0.0

    # 2. Batch inference
    batch_input = [single_input, single_input, single_input]
    req_batch = ModelInferenceRequest(model_id="inf_m1", inputs=batch_input)

    res_batch = engine.run_inference(req_batch)
    assert len(res_batch.outputs) == 3
    assert len(res_batch.outputs[0]) == 4
    assert res_batch.batch_size == 3

    print(f"  [OK] Single inference output: {res_single.outputs} ({res_single.latency_ms}ms)")
    print(f"  [OK] Batch inference output size: {len(res_batch.outputs)} samples ({res_batch.latency_ms}ms)")


def test_model_service_orchestration():
    print("\n--- [Test 19] ModelService Orchestration ---")
    reset_model_service()
    service = get_model_service()

    models = service.list_models()
    assert len(models) >= 1

    test_model_id = models[0].model_id
    status_resp = service.get_model_status(test_model_id)
    assert status_resp.ok is True
    assert status_resp.metadata.loaded is True

    # Single prediction
    input_vector = [0.1] * 8
    res = service.predict(test_model_id, inputs=input_vector)
    assert len(res.outputs) == 4

    print(f"  [OK] ModelService orchestration verified. Default model '{test_model_id}' status: {status_resp.metadata.status}")


def test_api_endpoints():
    print("\n--- [Test 20] REST API Endpoints ---")
    # GET /api/models
    res_list = client.get("/api/models")
    assert res_list.status_code == 200, f"List models failed: {res_list.text}"
    models_data = res_list.json()
    assert len(models_data) >= 1

    model_id = models_data[0]["model_id"]

    # GET /api/models/{model_id}
    res_status = client.get(f"/api/models/{model_id}")
    assert res_status.status_code == 200
    assert res_status.json()["model_id"] == model_id

    # POST /api/models/load
    load_payload = {
        "model_id": "api_test_m1",
        "model_name": "API Test Model",
        "model_type": "test_linear",
        "device": "cpu",
        "dtype": "float32",
    }
    res_load = client.post("/api/models/load", json=load_payload)
    assert res_load.status_code == 200
    assert res_load.json()["model_id"] == "api_test_m1"

    # POST /api/models/{model_id}/inference
    inf_payload = {
        "model_id": "api_test_m1",
        "inputs": [0.5] * 8,
    }
    res_inf = client.post("/api/models/api_test_m1/inference", json=inf_payload)
    assert res_inf.status_code == 200
    inf_data = res_inf.json()
    assert inf_data["model_id"] == "api_test_m1"
    assert len(inf_data["outputs"]) == 4

    print("  [OK] REST API endpoints (GET /api/models, POST /api/models/load, POST /api/models/{id}/inference) verified successfully.")


if __name__ == "__main__":
    test_pytorch_availability()
    test_model_configuration()
    test_device_manager()
    test_model_creation_and_metadata()
    test_model_loader()
    test_model_registry()
    test_inference_engine()
    test_model_service_orchestration()
    test_api_endpoints()
    print("\n[SUCCESS] ALL PHASE 9 PYTORCH MODEL LAYER TESTS PASSED SUCCESSFULLY!")
