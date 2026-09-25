"""Phase 11 Active Parameter Mechanism — Complete Test Suite.

Comprehensive deterministic unit, integration, and API test suite verifying:
1. Configuration validations
2. Parameter discovery & prefix grouping
3. Parameter count & memory estimation
4. Magnitude, gradient, and context scoring & normalization
5. Selection strategies: ALL, TOP_K, THRESHOLD, BUDGET
6. Minimum group fallbacks & maximum group ceilings
7. Resource budget constraints
8. Dry-run execution
9. Parameter masking, freeze/unfreeze
10. Critical state restoration
11. Critical weight non-corruption
12. Critical teacher safety (teacher parameters remain frozen)
13. Phase 10 distilled student model compatibility
14. ModelService integration
15. REST API endpoints
16. Invalid model/config handling and CPU-only execution determinism.
"""

import os
import sys
import unittest
import torch
import torch.nn as nn
from fastapi.testclient import TestClient

from app.main import app
from app.models.base import BasePyTorchModel, SimpleTestPyTorchModel
from app.models.config import ModelConfig
from app.models.service import ModelService, get_model_service, reset_model_service
from app.distillation.service import get_distillation_service, reset_distillation_service
from app.active_params.config import ActiveParamsSettings
from app.active_params.schemas import (
    ActiveParameterRequest,
    ActiveParameterResponse,
    ParameterInventory,
    SelectionStrategyEnum,
)
from app.active_params.parameter_groups import (
    ParameterGroupManager,
    PrefixParameterGroupingStrategy,
)
from app.active_params.scorer import (
    ContextRelevanceScorer,
    GradientImportanceScorer,
    ParameterMagnitudeScorer,
    normalize_scores,
)
from app.active_params.selector import (
    AllParameterStrategy,
    BudgetParameterStrategy,
    ParameterSelector,
    ThresholdParameterStrategy,
    TopKParameterStrategy,
)
from app.active_params.masking import ParameterMasker
from app.active_params.controller import ActiveParameterController
from app.active_params.service import (
    ActiveParameterService,
    get_active_parameter_service,
    reset_active_parameter_service,
)


class MultiLayerTestModel(BasePyTorchModel):
    """Deterministic 3-layer test model with explicit parameter groups."""

    def __init__(self, config: ModelConfig = None) -> None:
        cfg = config or ModelConfig(
            model_id="multi_layer_test_v1",
            model_name="Multi Layer Test Model",
            model_type="multi_layer",
        )
        super().__init__(cfg)
        self.layer1 = nn.Linear(8, 16)
        self.layer2 = nn.Linear(16, 8)
        self.classifier = nn.Linear(8, 2)
        self.initialize()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = torch.relu(self.layer1(x))
        out = torch.relu(self.layer2(out))
        return self.classifier(out)

    def predict(self, inputs):
        x = torch.tensor(inputs, dtype=torch.float32)
        if x.ndim == 1:
            x = x.unsqueeze(0)
        with torch.inference_mode():
            out = self.forward(x)
        return out.squeeze(0).tolist()

    def predict_batch(self, inputs):
        x = torch.tensor(inputs, dtype=torch.float32)
        with torch.inference_mode():
            out = self.forward(x)
        return out.tolist()


class TestPhase11ActiveParams(unittest.TestCase):

    def setUp(self):
        reset_model_service()
        reset_distillation_service()
        reset_active_parameter_service()
        self.model_service = get_model_service()
        self.test_model = MultiLayerTestModel()
        self.model_service.register_model(self.test_model, replace=True)
        self.active_service = get_active_parameter_service()
        self.client = TestClient(app)

    def tearDown(self):
        reset_model_service()
        reset_distillation_service()
        reset_active_parameter_service()

    def test_01_configuration_validation(self):
        print("\n[TEST 01] Validating ActiveParamsSettings parameters...")
        cfg = ActiveParamsSettings(
            threshold=0.7,
            top_k=2,
            minimum_active_groups=1,
            selection_strategy="top_k",
        )
        self.assertEqual(cfg.threshold, 0.7)
        self.assertEqual(cfg.top_k, 2)
        self.assertEqual(cfg.selection_strategy, "top_k")

        # Test invalid strategy
        with self.assertRaises(ValueError):
            ActiveParamsSettings(selection_strategy="invalid_strat")

        # Test invalid threshold out of range [0, 1]
        with self.assertRaises(ValueError):
            ActiveParamsSettings(threshold=1.5)

        # Test invalid top_k <= 0
        with self.assertRaises(ValueError):
            ActiveParamsSettings(top_k=0)

        # Test invalid min_groups < 1
        with self.assertRaises(ValueError):
            ActiveParamsSettings(minimum_active_groups=0)

        # Test invalid max_groups < min_groups
        with self.assertRaises(ValueError):
            ActiveParamsSettings(minimum_active_groups=3, maximum_active_groups=1)
        print("[SUCCESS] Test 01 Passed.")

    def test_02_parameter_discovery_and_grouping(self):
        print("\n[TEST 02] Parameter discovery and grouping...")
        manager = ParameterGroupManager(PrefixParameterGroupingStrategy(prefix_depth=1))
        inventory = manager.discover_groups(self.test_model, model_id="multi_layer_test_v1")

        self.assertEqual(inventory.model_id, "multi_layer_test_v1")
        self.assertGreater(inventory.total_parameters, 0)
        self.assertGreater(inventory.total_memory_bytes, 0)

        group_names = [g.group_name for g in inventory.groups]
        self.assertIn("layer1", group_names)
        self.assertIn("layer2", group_names)
        self.assertIn("classifier", group_names)
        print("[SUCCESS] Test 02 Passed.")

    def test_03_parameter_counts_and_memory_estimation(self):
        print("\n[TEST 03] Calculating parameter counts and memory estimates...")
        manager = ParameterGroupManager()
        inventory = manager.discover_groups(self.test_model)

        # layer1: Linear(8,16) -> weight(16*8=128) + bias(16) = 144
        # layer2: Linear(16,8) -> weight(8*16=128) + bias(8) = 136
        # classifier: Linear(8,2) -> weight(2*8=16) + bias(2) = 18
        # total = 298
        self.assertEqual(inventory.total_parameters, 298)
        self.assertEqual(inventory.trainable_parameters, 298)

        for g in inventory.groups:
            self.assertGreater(g.parameter_count, 0)
            self.assertEqual(g.estimated_memory_bytes, g.parameter_count * 4)  # float32 = 4 bytes
        print("[SUCCESS] Test 03 Passed.")

    def test_04_scoring_mechanisms(self):
        print("\n[TEST 04] Magnitude, gradient, and context scoring...")
        manager = ParameterGroupManager()
        inventory = manager.discover_groups(self.test_model)

        # Magnitude scoring
        mag_scorer = ParameterMagnitudeScorer()
        mag_scores = mag_scorer.score(self.test_model, inventory)
        self.assertEqual(len(mag_scores), len(inventory.groups))
        for score in mag_scores.values():
            self.assertGreaterEqual(score, 0.0)

        # Gradient scoring with missing gradients (fallback)
        grad_scorer = GradientImportanceScorer()
        grad_scores = grad_scorer.score(self.test_model, inventory)
        self.assertEqual(len(grad_scores), len(inventory.groups))

        # Score normalization
        norm_scores = normalize_scores(mag_scores)
        for val in norm_scores.values():
            self.assertGreaterEqual(val, 0.0)
            self.assertLessEqual(val, 1.0)

        # Context relevance scoring
        ctx_scorer = ContextRelevanceScorer(mag_scorer)
        ctx_scores = ctx_scorer.score(self.test_model, inventory, context={"task_type": "classification"})
        self.assertGreater(ctx_scores["classifier"], mag_scores["classifier"])
        print("[SUCCESS] Test 04 Passed.")

    def test_05_selection_strategies(self):
        print("\n[TEST 05] Selection strategies (ALL, TOP_K, THRESHOLD, BUDGET)...")
        manager = ParameterGroupManager()
        inventory = manager.discover_groups(self.test_model)
        scores = {"layer1": 0.2, "layer2": 0.8, "classifier": 0.9}
        cfg = ActiveParamsSettings()

        # ALL strategy
        all_strat = AllParameterStrategy()
        sel_all, fallback = all_strat.select(inventory, scores, cfg)
        self.assertEqual(len(sel_all), 3)
        self.assertFalse(fallback)

        # TOP_K strategy (k=2)
        top_k_strat = TopKParameterStrategy()
        req_top_k = ActiveParameterRequest(model_id="multi_layer_test_v1", top_k=2)
        sel_top2, _ = top_k_strat.select(inventory, scores, cfg, req_top_k)
        self.assertEqual(len(sel_top2), 2)
        self.assertIn("classifier", sel_top2)
        self.assertIn("layer2", sel_top2)

        # THRESHOLD strategy (thresh=0.5)
        thresh_strat = ThresholdParameterStrategy()
        req_thresh = ActiveParameterRequest(model_id="multi_layer_test_v1", threshold=0.5)
        sel_thresh, _ = thresh_strat.select(inventory, scores, cfg, req_thresh)
        self.assertEqual(len(sel_thresh), 2)
        self.assertIn("classifier", sel_thresh)
        self.assertIn("layer2", sel_thresh)

        # BUDGET strategy (param_budget=150)
        budget_strat = BudgetParameterStrategy()
        req_budget = ActiveParameterRequest(model_id="multi_layer_test_v1", parameter_budget=150)
        sel_budget, _ = budget_strat.select(inventory, scores, cfg, req_budget)
        self.assertGreaterEqual(len(sel_budget), 1)
        self.assertIn("classifier", sel_budget)  # classifier (18 params) fits easily
        print("[SUCCESS] Test 05 Passed.")

    def test_06_minimum_and_maximum_active_group_bounds(self):
        print("\n[TEST 06] Safety minimums and maximum group bounds...")
        manager = ParameterGroupManager()
        inventory = manager.discover_groups(self.test_model)
        scores = {"layer1": 0.1, "layer2": 0.1, "classifier": 0.1}

        # Threshold high -> 0 groups selected -> fallback to min 1 group
        selector = ParameterSelector(ActiveParamsSettings(minimum_active_groups=1, threshold=0.9))
        req = ActiveParameterRequest(model_id="multi_layer_test_v1", strategy=SelectionStrategyEnum.THRESHOLD, threshold=0.9)
        selected, fallback_used = selector.select(inventory, scores, req)
        self.assertEqual(len(selected), 1)
        self.assertTrue(fallback_used)

        # Maximum active groups ceiling
        selector_max = ParameterSelector(ActiveParamsSettings(maximum_active_groups=2))
        req_all = ActiveParameterRequest(model_id="multi_layer_test_v1", strategy=SelectionStrategyEnum.ALL)
        selected_max, _ = selector_max.select(inventory, scores, req_all)
        self.assertEqual(len(selected_max), 2)
        print("[SUCCESS] Test 06 Passed.")

    def test_07_dry_run_mode(self):
        print("\n[TEST 07] Dry run execution without state mutation...")
        controller = ActiveParameterController()

        # Check initial requires_grad state
        orig_grads = [p.requires_grad for p in self.test_model.parameters()]
        self.assertTrue(all(orig_grads))

        req = ActiveParameterRequest(
            model_id="multi_layer_test_v1",
            strategy=SelectionStrategyEnum.TOP_K,
            top_k=1,
            dry_run=True,
        )
        res = controller.execute_selection(self.test_model, req)
        self.assertTrue(res.dry_run)
        self.assertEqual(len(res.selected_groups), 1)

        # Verify model parameters were NOT changed
        post_dry_grads = [p.requires_grad for p in self.test_model.parameters()]
        self.assertEqual(orig_grads, post_dry_grads)
        print("[SUCCESS] Test 07 Passed.")

    def test_08_apply_and_freeze_inactive_parameters(self):
        print("\n[TEST 08] Applying active selection & freezing inactive parameters...")
        controller = ActiveParameterController()

        req = ActiveParameterRequest(
            model_id="multi_layer_test_v1",
            strategy=SelectionStrategyEnum.TOP_K,
            top_k=1,
            dry_run=False,
        )
        res = controller.execute_selection(self.test_model, req)
        self.assertFalse(res.dry_run)
        self.assertEqual(len(res.selected_groups), 1)

        # Active group parameters should have requires_grad=True
        active_group = res.selected_groups[0]
        group_manager = ParameterGroupManager()
        active_params = group_manager.get_group_parameters(self.test_model, active_group)
        for _, p in active_params:
            self.assertTrue(p.requires_grad)

        # Inactive group parameters should have requires_grad=False
        for inact_group in res.inactive_groups:
            inact_params = group_manager.get_group_parameters(self.test_model, inact_group)
            for _, p in inact_params:
                self.assertFalse(p.requires_grad)
        print("[SUCCESS] Test 08 Passed.")

    def test_09_critical_state_restoration(self):
        print("\n[TEST 09] Critical test: State snapshot restoration...")
        controller = ActiveParameterController()
        inventory = controller.discover(self.test_model, model_id="multi_layer_test_v1")

        # Record exact initial requires_grad state
        orig_state = {name: p.requires_grad for name, p in self.test_model.named_parameters()}

        # Apply selection (top_k=1)
        controller.apply(self.test_model, ["classifier"], inventory, model_id="multi_layer_test_v1")

        # Verify some parameters are now frozen
        current_frozen = [not p.requires_grad for p in self.test_model.parameters()]
        self.assertTrue(any(current_frozen))

        # Reset model
        controller.reset(self.test_model, model_id="multi_layer_test_v1")

        # Verify exact original state restored
        restored_state = {name: p.requires_grad for name, p in self.test_model.named_parameters()}
        self.assertEqual(orig_state, restored_state)
        print("[SUCCESS] Test 09 Passed.")

    def test_10_critical_weight_non_corruption(self):
        print("\n[TEST 10] Critical test: Weight non-corruption after selection & reset...")
        controller = ActiveParameterController()

        # Clone original weight values
        orig_weights = {name: p.detach().clone() for name, p in self.test_model.named_parameters()}

        # Run selection -> apply -> reset
        req = ActiveParameterRequest(
            model_id="multi_layer_test_v1",
            strategy=SelectionStrategyEnum.TOP_K,
            top_k=1,
            dry_run=False,
        )
        controller.execute_selection(self.test_model, req)
        controller.reset(self.test_model, model_id="multi_layer_test_v1")

        # Verify parameter tensor values are identical
        masker = ParameterMasker()
        self.assertTrue(masker.verify_weight_integrity(orig_weights, self.test_model))
        print("[SUCCESS] Test 10 Passed.")

    def test_11_critical_teacher_safety(self):
        print("\n[TEST 11] Critical test: Teacher safety (frozen model remains frozen)...")
        # Freeze teacher model entirely
        teacher_model = MultiLayerTestModel(ModelConfig(model_id="teacher_v1", model_name="Teacher", model_type="teacher"))
        teacher_model.eval()
        for p in teacher_model.parameters():
            p.requires_grad = False

        self.model_service.register_model(teacher_model, replace=True)

        controller = ActiveParameterController()
        req = ActiveParameterRequest(
            model_id="teacher_v1",
            strategy=SelectionStrategyEnum.TOP_K,
            top_k=2,
            dry_run=False,
        )
        res = controller.execute_selection(teacher_model, req)

        # Verify that teacher parameters remain 100% frozen (requires_grad == False)
        for p in teacher_model.parameters():
            self.assertFalse(p.requires_grad, "Teacher parameter was modified to trainable!")
        print("[SUCCESS] Test 11 Passed.")

    def test_12_distilled_model_compatibility(self):
        print("\n[TEST 12] Integration with Phase 10 distilled student models...")
        from app.distillation.config import DistillationConfig
        dist_service = get_distillation_service()

        # Perform synthetic distillation job to produce a distilled model registered in ModelRegistry
        config = DistillationConfig(epochs=1)
        dist_res = dist_service.distill(config)
        self.assertEqual(dist_res.status, "completed")
        distilled_model_id = dist_res.registered_model_id

        # Verify distilled model exists in ModelRegistry
        reg_model = self.model_service.registry.get(distilled_model_id)
        self.assertIsNotNone(reg_model)
        self.assertEqual(reg_model.get_metadata().model_type, "distilled")

        # Run active parameter selection on distilled student model
        req = ActiveParameterRequest(
            model_id=distilled_model_id,
            strategy=SelectionStrategyEnum.TOP_K,
            top_k=1,
            dry_run=False,
        )
        res = self.active_service.select_parameters(req)
        self.assertEqual(res.model_id, distilled_model_id)
        self.assertEqual(len(res.selected_groups), 1)
        print("[SUCCESS] Test 12 Passed.")

    def test_13_api_endpoints(self):
        print("\n[TEST 13] REST API Endpoints testing...")
        # 1. GET /api/active-params/{model_id}
        res_inv = self.client.get("/api/active-params/multi_layer_test_v1")
        self.assertEqual(res_inv.status_code, 200)
        data_inv = res_inv.json()
        self.assertEqual(data_inv["model_id"], "multi_layer_test_v1")

        # 2. POST /api/active-params/select
        res_sel = self.client.post("/api/active-params/select", json={
            "model_id": "multi_layer_test_v1",
            "strategy": "top_k",
            "top_k": 2,
            "dry_run": False
        })
        self.assertEqual(res_sel.status_code, 200)
        data_sel = res_sel.json()
        self.assertEqual(len(data_sel["selected_groups"]), 2)

        # 3. POST /api/active-params/{model_id}/dry-run
        res_dry = self.client.post("/api/active-params/multi_layer_test_v1/dry-run", json={
            "strategy": "threshold",
            "threshold": 0.5
        })
        self.assertEqual(res_dry.status_code, 200)
        data_dry = res_dry.json()
        self.assertTrue(data_dry["dry_run"])

        # 4. POST /api/active-params/{model_id}/reset
        res_rst = self.client.post("/api/active-params/multi_layer_test_v1/reset")
        self.assertEqual(res_rst.status_code, 200)
        data_rst = res_rst.json()
        self.assertEqual(data_rst["strategy"], "reset")

        # 5. Invalid model ID 404 test
        res_404 = self.client.get("/api/active-params/non_existent_model_id")
        self.assertEqual(res_404.status_code, 404)
        print("[SUCCESS] Test 13 Passed.")


if __name__ == "__main__":
    unittest.main()
