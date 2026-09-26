"""Phase 6 — Real QUBO Optimization Test Suite.

Verifies:
1. QUBO matrix shape (N x N)
2. Deterministic candidate ordering
3. Binary variable validation
4. QUBO energy calculation x^T Q x
5. Cardinality penalty P*(sum x_i - K)^2
6. Redundancy penalty lambda * sum S_ij x_i x_j
7. Relevance reward -alpha * sum R_i x_i
8. Graph reward -beta * sum G_i x_i
9. Objective decomposition
10. Exact solver (N <= 12 exhaustive search)
11. Simulated annealing solver
12. Deterministic seed behavior
13. Target-K selection
14. Ground-truth exhaustive search comparison (N <= 12)
15. Simulated annealing energy >= exact optimum
16. Provenance preservation
17. API endpoint POST /api/qubo/optimize
18. Status endpoint GET /api/qubo/status
19. Phase 5 -> QUBO integration
20. Selected evidence quality
"""
from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.optimization.config import OptimizationConfig
from app.optimization.qubo_matrix import (
    QUBOFormulator,
    evaluate_objective_breakdown,
    qubo_energy,
)
from app.optimization.schemas import CandidateFeatureVector
from app.optimization.solvers import (
    ExactQUBOSolver,
    SimulatedAnnealingQUBOSolver,
    get_qubo_solver,
)
from app.rag.hybrid_retriever import HybridRetriever

client = TestClient(app)


def make_dummy_candidates(n: int) -> list[CandidateFeatureVector]:
    """Helper to generate n deterministic candidates."""
    candidates = []
    for i in range(n):
        candidates.append(
            CandidateFeatureVector(
                candidate_id=f"cand_{i:03d}",
                source_type="vector" if i % 2 == 0 else "graph",
                document_id="doc_test_report",
                text=f"Sample text content for candidate {i} with key data points {i * 10}% performance metric.",
                relevance_score=0.9 - (i * 0.05),
                graph_score=0.8 - (i * 0.04),
                evidence_quality=0.95,
            )
        )
    return candidates


class TestQUBOFormulation:
    """Tests 1–9: Mathematical matrix construction and energy evaluation."""

    def test_01_qubo_matrix_shape(self):
        candidates = make_dummy_candidates(8)
        formulator = QUBOFormulator()
        problem = formulator.build_qubo(candidates, target_k=3)
        assert len(problem.matrix) == 8
        for row in problem.matrix:
            assert len(row) == 8

    def test_02_deterministic_candidate_ordering(self):
        candidates = make_dummy_candidates(5)
        import random
        shuffled = list(candidates)
        random.shuffle(shuffled)
        formulator = QUBOFormulator()
        prob1 = formulator.build_qubo(candidates, target_k=2)
        prob2 = formulator.build_qubo(shuffled, target_k=2)
        assert prob1.candidate_ids == prob2.candidate_ids == ["cand_000", "cand_001", "cand_002", "cand_003", "cand_004"]

    def test_03_binary_variable_validation(self):
        candidates = make_dummy_candidates(4)
        formulator = QUBOFormulator()
        prob = formulator.build_qubo(candidates, target_k=2)
        x_valid = [1, 0, 1, 0]
        energy = qubo_energy(prob.matrix, x_valid, prob.constant_offset)
        assert isinstance(energy, float)

    def test_04_qubo_energy_calculation(self):
        # 2x2 matrix
        Q = [[-2.0, 1.5], [0.0, -3.0]]
        x = [1, 1]
        # x^T Q x = Q_00*1 + Q_11*1 + Q_01*1*1 = -2.0 + -3.0 + 1.5 = -3.5
        assert qubo_energy(Q, x, constant_offset=0.0) == -3.5

    def test_05_cardinality_penalty(self):
        candidates = make_dummy_candidates(4)
        weights = {"cardinality_penalty": 5.0, "relevance_weight": 0.0, "graph_weight": 0.0, "diversity_weight": 0.0, "redundancy_weight": 0.0}
        formulator = QUBOFormulator()
        prob = formulator.build_qubo(candidates, target_k=2, weights=weights)

        # Select 2 items -> penalty = 5.0 * (2 - 2)^2 = 0
        x_k2 = [1, 1, 0, 0]
        decomp_k2 = evaluate_objective_breakdown(prob.candidates, x_k2, target_k=2, weights=weights)
        assert decomp_k2["cardinality_penalty"] == 0.0

        # Select 3 items -> penalty = 5.0 * (3 - 2)^2 = 5.0
        x_k3 = [1, 1, 1, 0]
        decomp_k3 = evaluate_objective_breakdown(prob.candidates, x_k3, target_k=2, weights=weights)
        assert decomp_k3["cardinality_penalty"] == 5.0

    def test_06_redundancy_penalty(self):
        c1 = CandidateFeatureVector(candidate_id="c1", text="apple banana orange", relevance_score=0.5)
        c2 = CandidateFeatureVector(candidate_id="c2", text="apple banana orange", relevance_score=0.5)
        weights = {"redundancy_weight": 2.0, "relevance_weight": 0.0, "graph_weight": 0.0, "diversity_weight": 0.0, "cardinality_penalty": 0.0}

        decomp = evaluate_objective_breakdown([c1, c2], [1, 1], target_k=2, weights=weights)
        assert decomp["redundancy_penalty"] > 0.0

    def test_07_relevance_reward(self):
        c1 = CandidateFeatureVector(candidate_id="c1", text="a", relevance_score=0.9)
        weights = {"relevance_weight": 1.0, "graph_weight": 0.0, "diversity_weight": 0.0, "redundancy_weight": 0.0, "cardinality_penalty": 0.0}
        decomp = evaluate_objective_breakdown([c1], [1], target_k=1, weights=weights)
        assert decomp["relevance_reward"] == -0.9

    def test_08_graph_reward(self):
        c1 = CandidateFeatureVector(candidate_id="c1", text="a", graph_score=0.8)
        weights = {"graph_weight": 0.7, "relevance_weight": 0.0, "diversity_weight": 0.0, "redundancy_weight": 0.0, "cardinality_penalty": 0.0}
        decomp = evaluate_objective_breakdown([c1], [1], target_k=1, weights=weights)
        assert round(decomp["graph_reward"], 2) == -0.56

    def test_09_objective_decomposition(self):
        candidates = make_dummy_candidates(5)
        formulator = QUBOFormulator()
        prob = formulator.build_qubo(candidates, target_k=2)
        x = [1, 1, 0, 0, 0]

        q_energy = qubo_energy(prob.matrix, x, prob.constant_offset)
        decomp = evaluate_objective_breakdown(prob.candidates, x, target_k=2, weights=prob.weights)
        assert abs(q_energy - decomp["total_energy"]) < 1e-3


class TestQUBOSolvers:
    """Tests 10–15: Solvers, ground truth exhaustive comparison, and reproducibility."""

    def test_10_exact_solver_small_problem(self):
        candidates = make_dummy_candidates(6)
        formulator = QUBOFormulator()
        prob = formulator.build_qubo(candidates, target_k=3)
        solver = ExactQUBOSolver()
        res = solver.solve(prob)

        assert res.solver_type == "classical_exact"
        assert len(res.selected_candidate_ids) > 0
        assert res.total_energy is not None

    def test_11_simulated_annealing_solver(self):
        candidates = make_dummy_candidates(10)
        formulator = QUBOFormulator()
        prob = formulator.build_qubo(candidates, target_k=4)
        solver = SimulatedAnnealingQUBOSolver()
        res = solver.solve(prob)

        assert res.solver_type == "classical_simulated_annealing"
        assert len(res.selected_candidate_ids) > 0

    def test_12_deterministic_seed_behavior(self):
        candidates = make_dummy_candidates(15)
        formulator = QUBOFormulator()
        prob = formulator.build_qubo(candidates, target_k=5)

        cfg1 = OptimizationConfig(seed=123)
        cfg2 = OptimizationConfig(seed=123)
        res1 = SimulatedAnnealingQUBOSolver(cfg1).solve(prob)
        res2 = SimulatedAnnealingQUBOSolver(cfg2).solve(prob)

        assert res1.binary_solution == res2.binary_solution
        assert res1.total_energy == res2.total_energy

    def test_13_target_k_selection(self):
        candidates = make_dummy_candidates(8)
        formulator = QUBOFormulator()
        prob = formulator.build_qubo(candidates, target_k=3)
        res = ExactQUBOSolver().solve(prob)

        assert sum(res.binary_solution) == 3

    def test_14_exhaustive_ground_truth_comparison(self):
        """CRITICAL TEST: Verify ExactQUBOSolver matches manual 2^N brute force minimum."""
        candidates = make_dummy_candidates(7)
        formulator = QUBOFormulator()
        prob = formulator.build_qubo(candidates, target_k=3)

        # 1. ExactQUBOSolver
        exact_res = ExactQUBOSolver().solve(prob)

        # 2. Independent 2^N loop
        n = len(candidates)
        min_e = float("inf")
        best_bits = []
        for i in range(1 << n):
            bits = [(i >> b) & 1 for b in range(n)]
            e = qubo_energy(prob.matrix, bits, prob.constant_offset)
            if e < min_e:
                min_e = e
                best_bits = bits

        assert exact_res.total_energy == round(min_e, 4)
        assert exact_res.binary_solution == best_bits

    def test_15_simulated_annealing_energy_bound(self):
        """Verify SA energy is >= exact minimum energy for small problem."""
        candidates = make_dummy_candidates(8)
        formulator = QUBOFormulator()
        prob = formulator.build_qubo(candidates, target_k=3)

        exact_res = ExactQUBOSolver().solve(prob)
        sa_res = SimulatedAnnealingQUBOSolver().solve(prob)

        assert sa_res.total_energy >= exact_res.total_energy - 1e-4


class TestIntegrationAndAPI:
    """Tests 16–20: Provenance, API routes, and HybridRetriever integration."""

    def test_16_provenance_preservation(self):
        candidates = make_dummy_candidates(6)
        formulator = QUBOFormulator()
        prob = formulator.build_qubo(candidates, target_k=2)
        res = ExactQUBOSolver().solve(prob)

        selected_set = set(res.selected_candidate_ids)
        assert len(selected_set) == 2
        for cand in candidates:
            if cand.candidate_id in selected_set:
                assert cand.document_id == "doc_test_report"
                assert "Sample text content" in cand.text

    def test_17_api_qubo_optimize_endpoint(self):
        payload = {
            "candidates": [
                {"candidate_id": "c1", "text": "CatBoost accuracy 97.5%", "relevance_score": 0.9, "document_id": "doc1"},
                {"candidate_id": "c2", "text": "Random Forest precision 94.2%", "relevance_score": 0.8, "document_id": "doc1"},
                {"candidate_id": "c3", "text": "IoT ESP32 sensor node", "relevance_score": 0.7, "document_id": "doc2"},
            ],
            "target_k": 2,
            "solver": "exact",
        }
        resp = client.post("/api/qubo/optimize", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["solver_type"] == "classical_exact"
        assert data["target_k"] == 2
        assert len(data["selected_candidate_ids"]) == 2
        assert "objective_breakdown" in data

    def test_18_api_qubo_status_endpoint(self):
        resp = client.get("/api/qubo/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["enabled"] is True
        assert "quantum_backend_available" in data

    def test_19_phase5_hybrid_retriever_qubo_integration(self):
        retriever = HybridRetriever()
        results, metrics = retriever.retrieve(query="banana ripeness classification", top_k=3, enable_qubo=True)

        assert len(results) <= 3
        assert "qubo_optimization_time_ms" in metrics
        for item in results:
            assert "selected_by_qubo" in item
            assert "document_id" in item
            assert "text" in item

    def test_20_selected_evidence_quality(self):
        retriever = HybridRetriever()
        results, _ = retriever.retrieve(query="CatBoost performance values", top_k=3, enable_qubo=True)
        assert len(results) > 0
        for res in results:
            assert len(res["text"]) > 0
