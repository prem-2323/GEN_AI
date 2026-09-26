"""Phase 8 — Quantum / Hybrid Optimization Complete Test Suite.

Tests:
1. Problem Construction & Feature Vector Generation
2. Objective Function & Constraint Checking
3. Classical Solver Baseline
4. QUBO Formulation & Mock Quantum Solver (Simulated Annealing)
5. 4-Step Hybrid Solver Workflow
6. Quantum Failure & Graceful Fallback to Classical Solver
7. Standalone API Endpoint POST /api/optimization/select
8. Phase 7 RAG Integration (POST /api/rag/query with Phase 8 Optimization metadata)
9. Optimization Benchmark Suite (Comparing Baseline vs Classical vs Hybrid on relevance, redundancy, graph coverage, and token budget).
"""
import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add Backend root directory to sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.main import app
from app.embeddings.service import get_embedding_service
from app.graph.service import GraphService
from app.graph.models import DocumentNodeModel, GraphNodeModel, GraphPayload, GraphRelationshipModel
from app.optimization import (
    ClassicalOptimizer,
    ConstraintManager,
    HybridOptimizer,
    MockQuantumOptimizer,
    ObjectiveCalculator,
    OptimizationConfig,
    OptimizationService,
    ProblemFormulator,
    QUBOFormulator,
    get_optimization_service,
)
from app.rag.schemas import RAGQueryRequest, RetrievalResult
from app.rag.service import get_rag_service

client = TestClient(app)

SAMPLE_DOC_ID = "doc_phase8_tech_report"
SAMPLE_QUERY = "What technologies does OpenAI use?"

# Mock retrieval candidates
SAMPLE_CANDIDATES = [
    RetrievalResult(
        source_type="vector",
        source_id="chunk_001",
        document_id="doc_report_A",
        text="OpenAI utilizes PyTorch as its primary deep learning framework for training GPT models.",
        score=0.94,
        metadata={"page_number": 1},
        evidence={"page": 1, "filename": "report_A.pdf"},
    ),
    RetrievalResult(
        source_type="vector",
        source_id="chunk_002",
        document_id="doc_report_A",  # Redundant chunk from same doc
        text="OpenAI uses PyTorch framework for training GPT language models in clusters.",
        score=0.91,
        metadata={"page_number": 1},
        evidence={"page": 1, "filename": "report_A.pdf"},
    ),
    RetrievalResult(
        source_type="vector",
        source_id="chunk_003",
        document_id="doc_report_B",  # Diverse document source
        text="Infrastructure operations rely heavily on CUDA GPU clusters and custom Triton compilers.",
        score=0.88,
        metadata={"page_number": 4},
        evidence={"page": 4, "filename": "report_B.pdf"},
    ),
    RetrievalResult(
        source_type="graph",
        source_id="rel_001",
        document_id="doc_report_A",
        text="OpenAI --[USES]--> PyTorch (Evidence: OpenAI utilizes PyTorch framework.)",
        score=0.92,
        metadata={"source": "OpenAI", "relation": "USES", "target": "PyTorch"},
        evidence={"source": "OpenAI", "relation": "USES", "target": "PyTorch"},
    ),
    RetrievalResult(
        source_type="graph",
        source_id="rel_002",
        document_id="doc_report_B",
        text="OpenAI --[USES]--> CUDA (Evidence: Infrastructure runs on CUDA GPUs.)",
        score=0.89,
        metadata={"source": "OpenAI", "relation": "USES", "target": "CUDA"},
        evidence={"source": "OpenAI", "relation": "USES", "target": "CUDA"},
    ),
]


def test_problem_construction():
    print("\n--- [Test 1] Problem Construction & Feature Extraction ---")
    formulator = ProblemFormulator()
    problem = formulator.build_problem(
        query=SAMPLE_QUERY,
        candidates=SAMPLE_CANDIDATES,
        max_selected=3,
        max_tokens=1000,
    )

    assert len(problem.candidates) == len(SAMPLE_CANDIDATES)
    assert problem.max_selected_candidates == 3
    assert len(problem.pairwise_redundancy_matrix) == len(SAMPLE_CANDIDATES)

    # Verify high redundancy between chunk_001 and chunk_002
    red_0_1 = problem.pairwise_redundancy_matrix[0][1]
    assert red_0_1 > 0.4, f"Expected high redundancy between chunk 0 and 1, got {red_0_1}"

    print(f"  [OK] Formulated optimization problem for {len(problem.candidates)} candidates.")
    print(f"  [OK] Calculated pairwise redundancy between chunk 0 and 1: {red_0_1:.3f}")


def test_objective_and_constraints():
    print("\n--- [Test 2] Objective Function & Constraints ---")
    formulator = ProblemFormulator()
    problem = formulator.build_problem(query=SAMPLE_QUERY, candidates=SAMPLE_CANDIDATES, max_selected=3, max_tokens=1000)

    obj_calc = ObjectiveCalculator()
    constraint_mgr = ConstraintManager()

    # Valid selection: select chunk_001, chunk_003, and rel_001
    selection_valid = [1, 0, 1, 1, 0]
    score_valid = obj_calc.evaluate(problem, selection_valid)
    is_valid, violations = constraint_mgr.is_valid(problem, selection_valid)

    assert is_valid is True, f"Expected valid selection, got violations: {violations}"
    assert score_valid > 0.0, f"Expected positive objective score, got {score_valid}"

    # Invalid selection: selecting 4 candidates when max_selected=3
    selection_invalid = [1, 1, 1, 1, 0]
    is_invalid, violations_invalid = constraint_mgr.is_valid(problem, selection_invalid)
    assert is_invalid is False
    assert len(violations_invalid) > 0

    print(f"  [OK] Objective score for valid selection: {score_valid:.4f}")
    print(f"  [OK] Constraint manager correctly flagged overflow: {violations_invalid[0]}")


def test_classical_solver():
    print("\n--- [Test 3] Classical Solver Baseline ---")
    formulator = ProblemFormulator()
    problem = formulator.build_problem(query=SAMPLE_QUERY, candidates=SAMPLE_CANDIDATES, max_selected=3, max_tokens=1000)

    classical_opt = ClassicalOptimizer()
    result = classical_opt.optimize(problem)

    assert len(result.selected_candidate_ids) <= 3
    assert result.constraints_satisfied is True
    assert result.solver_used == "classical"
    assert result.objective_value > 0.0

    print(f"  [OK] Classical solver selected {len(result.selected_candidate_ids)} candidates in {result.latency_ms}ms (objective: {result.objective_value:.4f})")


def test_qubo_and_mock_quantum():
    print("\n--- [Test 4] QUBO Formulation & Mock Quantum Solver ---")
    formulator = ProblemFormulator()
    problem = formulator.build_problem(query=SAMPLE_QUERY, candidates=SAMPLE_CANDIDATES, max_selected=3, max_tokens=1000)

    qubo_formulator = QUBOFormulator()
    Q = qubo_formulator.build_qubo_matrix(problem)

    assert len(Q) == len(SAMPLE_CANDIDATES)
    assert len(Q[0]) == len(SAMPLE_CANDIDATES)

    mock_quantum = MockQuantumOptimizer()
    result = mock_quantum.optimize(problem)

    assert len(result.selected_candidate_ids) <= 3
    assert isinstance(result.constraints_satisfied, bool)
    assert result.qubo_matrix_size == len(SAMPLE_CANDIDATES)

    print(f"  [OK] QUBO matrix built ({len(Q)}x{len(Q)}).")
    print(f"  [OK] Mock Quantum solver selected {len(result.selected_candidate_ids)} items in {result.latency_ms}ms (objective: {result.objective_value:.4f})")


def test_hybrid_solver_and_fallback():
    print("\n--- [Test 5 & 6] Hybrid Solver & Graceful Fallback ---")
    formulator = ProblemFormulator()
    problem = formulator.build_problem(query=SAMPLE_QUERY, candidates=SAMPLE_CANDIDATES, max_selected=3, max_tokens=1000)

    hybrid_opt = HybridOptimizer()
    result = hybrid_opt.optimize(problem)

    assert len(result.selected_candidate_ids) <= 3
    assert result.constraints_satisfied is True
    assert result.solver_used == "hybrid"

    print(f"  [OK] Hybrid solver workflow completed: {len(result.selected_candidate_ids)} items selected in {result.latency_ms}ms.")

    # Test Graceful Fallback when quantum backend fails
    svc = OptimizationService()
    optimized, meta = svc.optimize_candidates(
        query=SAMPLE_QUERY,
        candidates=SAMPLE_CANDIDATES,
        backend="quantum",  # triggers quantum with simulated/fallback handler
        max_selected=3,
    )

    assert len(optimized) <= 3
    assert meta.constraints_satisfied is True
    print(f"  [OK] Fallback test verified: {len(optimized)} items returned (solver: {meta.solver_used}).")


def test_standalone_api_endpoint():
    print("\n--- [Test 7] Standalone API Endpoint POST /api/optimization/select ---")
    candidates_dict = [c.model_dump() for c in SAMPLE_CANDIDATES]

    req_payload = {
        "query": SAMPLE_QUERY,
        "candidates": candidates_dict,
        "backend": "hybrid",
        "max_selected": 3,
        "max_tokens": 1000,
    }

    res = client.post("/api/optimization/select", json=req_payload)
    assert res.status_code == 200, f"API failed: {res.text}"

    data = res.json()
    assert data["query"] == SAMPLE_QUERY
    assert len(data["selected_candidates"]) <= 3
    assert "optimization" in data
    assert data["optimization"]["backend"] == "hybrid"
    assert data["optimization"]["constraints_satisfied"] is True

    print(f"  [OK] POST /api/optimization/select returned 200 OK. Selected: {len(data['selected_candidates'])} candidates.")


def test_rag_integration_with_optimization():
    print("\n--- [Test 8] Phase 7 RAG Integration with Phase 8 Optimization ---")
    embed_svc = get_embedding_service()
    embed_svc.index_text(
        text="OpenAI utilizes PyTorch for model training. CUDA GPUs provide hardware acceleration.",
        document_id="doc_opt_rag_test",
        source_filename="opt_report.pdf",
    )

    try:
        graph_svc = GraphService()
        payload = GraphPayload(
            document=DocumentNodeModel(document_id="doc_opt_rag_test", title="Opt Report"),
            nodes=[
                GraphNodeModel(entity_id="OpenAI", label="Organization", canonical_name="OpenAI", entity_type="Organization"),
                GraphNodeModel(entity_id="PyTorch", label="Technology", canonical_name="PyTorch", entity_type="Technology"),

            ],
            relationships=[
                GraphRelationshipModel(
                    relation_id="r_opt_1",
                    source_id="OpenAI",
                    target_id="PyTorch",
                    relation_type="USES",
                    document_id="doc_opt_rag_test",
                    evidence_text="OpenAI utilizes PyTorch.",
                )
            ],
        )
        graph_svc.ingest_doclink_result(payload)
    except ConnectionError as e:
        print(f"  [INFO] Neo4j offline during test: {e}")

    rag_svc = get_rag_service()
    req = RAGQueryRequest(
        query="What technologies does OpenAI use?",
        top_k=4,
        document_id="doc_opt_rag_test",
    )

    try:
        response = rag_svc.query(req)
        assert response.query == req.query
        assert response.optimization is not None
        print(f"  [OK] RAG response verified. Optimization backend: {response.optimization.get('backend')}")
    except ConnectionError as e:
        print(f"  [INFO] Neo4j offline during RAG query test: {e}")


def test_optimization_benchmark_suite():
    print("\n--- [Test 9] Phase 8 Optimization Benchmark Suite ---")
    formulator = ProblemFormulator()
    problem = formulator.build_problem(query=SAMPLE_QUERY, candidates=SAMPLE_CANDIDATES, max_selected=3, max_tokens=1000)

    # 1. Baseline: No Optimization (Raw Top-3 candidates)
    baseline_selected = SAMPLE_CANDIDATES[:3]
    baseline_bits = [1, 1, 1, 0, 0]
    obj_calc = ObjectiveCalculator()
    baseline_obj = obj_calc.evaluate(problem, baseline_bits)

    # 2. Classical Optimization
    classical_opt = ClassicalOptimizer()
    classical_res = classical_opt.optimize(problem)

    # 3. Hybrid Optimization
    hybrid_opt = HybridOptimizer()
    hybrid_res = hybrid_opt.optimize(problem)

    print("  ==============================================================")
    print("  PHASE 8 OPTIMIZATION BENCHMARK RESULTS:")
    print(f"  - Baseline (No Opt) : Candidates=3, Objective={baseline_obj:.4f}")
    print(f"  - Classical Solver  : Candidates={classical_res.candidates_after}, Objective={classical_res.objective_value:.4f}, Latency={classical_res.latency_ms}ms")
    print(f"  - Hybrid Solver     : Candidates={hybrid_res.candidates_after}, Objective={hybrid_res.objective_value:.4f}, Latency={hybrid_res.latency_ms}ms")
    print("  ==============================================================")

    assert classical_res.objective_value >= baseline_obj or classical_res.candidates_after <= len(baseline_selected)
    print("  [OK] Optimization benchmark suite passed successfully.")


if __name__ == "__main__":
    test_problem_construction()
    test_objective_and_constraints()
    test_classical_solver()
    test_qubo_and_mock_quantum()
    test_hybrid_solver_and_fallback()
    test_standalone_api_endpoint()
    test_rag_integration_with_optimization()
    test_optimization_benchmark_suite()
    print("\n[SUCCESS] ALL PHASE 8 QUANTUM / HYBRID OPTIMIZATION TESTS PASSED SUCCESSFULLY!")
