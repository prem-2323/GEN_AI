# Phase 6 — QUBO Architecture Audit & Inspection

**Date**: 2026-09-26  
**Project**: Gen-Transform-AI  
**Phase**: Phase 6 — REAL QUBO Optimization for Evidence Selection  

---

## 1. Current QUBO Architecture Overview

The existing codebase in `app/optimization` contains a preliminary framework for candidate selection optimization. However, several mock/simulated behaviors exist that need to be upgraded or replaced to establish a mathematically **real** QUBO optimization layer.

### 1.1 Existing Flow & Data Ingestion
1. Candidates are represented as `CandidateFeatureVector` instances inside `OptimizationProblemSchema`.
2. Candidates are ingested from `RetrievalResult` objects.
3. `ProblemFormulator` computes a pairwise redundancy matrix using simple text character n-gram/word overlap.
4. `QUBOFormulator` builds an $N \times N$ matrix $Q$ combining linear diagonal utility scores and quadratic off-diagonal redundancy penalties.
5. `MockQuantumOptimizer` executes a basic local simulated annealing loop over binary vectors $x \in \{0,1\}^N$, but labels its solver output as `"mock_quantum"`.
6. `QuantumOptimizer` checks for live quantum SDKs and falls back to `MockQuantumOptimizer` labeled as `"quantum_simulated"`.

---

## 2. Identified Gaps & Mock Behaviors

| Component | Current Implementation | Identified Defect / Required Phase 6 Upgrade |
| :--- | :--- | :--- |
| **Solver Naming** | Solvers return `"mock_quantum"` and `"quantum_simulated"`. | **Violation**: Calling classical algorithms "quantum". Must be strictly renamed to `classical_exact` or `classical_simulated_annealing`. |
| **QUBO Formulation** | `QUBOFormulator` uses ad-hoc linear utility ($-\text{utility}$) and fixed pairwise penalties ($red \cdot w_{red} + doc\_collision$). | **Lacks explicit mathematical formulation**: Missing exact target cardinality penalty expansion $P(\sum x_i - K)^2$, exact semantic/graph/diversity decomposition, and symmetric/upper-triangular matrix specification. |
| **Cardinality Penalty** | Handled via soft constraint manager evaluation during simulated annealing instead of directly inside the QUBO energy matrix $x^T Q x$. | **Requirement**: Hard/soft cardinality penalty $P(\sum x_i - K)^2 = P(\sum (1-2K)x_i + 2\sum_{i<j} x_i x_j + K^2)$ must be baked into matrix $Q$. |
| **Exact Solver** | Missing. | **Requirement**: Need an exact $2^N$ exhaustive solver for $N \le 12$ to establish ground-truth optimal solution. |
| **Simulated Annealing** | Basic random walk without explicit seed control or deterministic test guarantees. | **Requirement**: Implement reproducible classical simulated annealing over binary variables $x_i \in \{0,1\}$. |
| **RAG Integration** | Optimization was invoked in `select_optimal_candidates` route but not directly cleanly hooked into Phase 5 hybrid retrieval pipeline with full provenance preservation. | **Requirement**: Integrate QUBO candidate selection stage cleanly post-RRF fusion, preserving all provenance metadata (`document_id`, `chunk_id`, `page_number`, `scores`, `selected_by_qubo`). |
| **API & Status** | Standalone POST `/api/optimization/select` exists; `/api/qubo/optimize` and `/api/qubo/status` missing. | **Requirement**: Implement `/api/qubo/optimize` and `/api/qubo/status`. |

---

## 3. Mathematical Specification for Phase 6 QUBO

The objective function to minimize over binary vector $x \in \{0,1\}^N$ ($x_i = 1$ if candidate $i$ is selected, $0$ otherwise) is defined as:

$$E(x) = x^T Q x$$

Expanded into physical component terms:

$$E(x) = -\alpha \sum_{i=1}^N R_i x_i - \beta \sum_{i=1}^N G_i x_i - \gamma \sum_{i=1}^N D_i x_i + \lambda \sum_{1 \le i < j \le N} S_{ij} x_i x_j + P \left( \sum_{i=1}^N x_i - K \right)^2$$

### Cardinality Penalty Matrix Expansion:
Since $x_i^2 = x_i$ for binary $x_i \in \{0,1\}$:

$$P \left( \sum_{i=1}^N x_i - K \right)^2 = P \left[ \sum_{i=1}^N (1 - 2K) x_i + 2 \sum_{1 \le i < j \le N} x_i x_j + K^2 \right]$$

### Full QUBO Matrix Coefficients ($Q$):
- **Diagonal Coefficients ($Q_{ii}$)**:
  $$Q_{ii} = -\alpha R_i - \beta G_i - \gamma D_i + P(1 - 2K)$$
- **Off-Diagonal Upper-Triangular Coefficients ($Q_{ij}$ for $i < j$)**:
  $$Q_{ij} = \lambda S_{ij} + 2P$$
- **Constant Energy Offset**: $C = P \cdot K^2$

---

## 4. Planned Code Changes & File Impact

### Files to be Modified / Created:

1. **`app/optimization/qubo_matrix.py`** (NEW)
   - Implement `QUBOProblem`, `QUBOFormulator`, `qubo_energy()`, `evaluate_objective_breakdown()`, matrix $Q$ builder, validation, and energy decomposition.
2. **`app/optimization/solvers.py`** (NEW / Refactored)
   - Implement abstract `QUBOSolver`, `ExactQUBOSolver` ($N \le 12$ exhaustive search), `SimulatedAnnealingQUBOSolver` (reproducible SA), and optional `DWaveQUBOSolver` (reporting `quantum_backend_available = false`).
3. **`app/optimization/config.py`** (UPDATED)
   - Add environment variable configuration for `QUBO_ENABLED`, `QUBO_SOLVER`, `QUBO_RELEVANCE_WEIGHT`, `QUBO_GRAPH_WEIGHT`, `QUBO_DIVERSITY_WEIGHT`, `QUBO_REDUNDANCY_WEIGHT`, `QUBO_CARDINALITY_PENALTY`, `QUBO_SEED`, `QUBO_ANNEALING_STEPS`, `QUBO_INITIAL_TEMPERATURE`, `QUBO_FINAL_TEMPERATURE`.
4. **`app/api/routes/qubo.py`** (NEW)
   - Implement `POST /api/qubo/optimize` and `GET /api/qubo/status`. Include router in `app/main.py`.
5. **`app/rag/hybrid_retriever.py`** (UPDATED)
   - Integrate optional QUBO evidence selection post RRF deduplication.
6. **`tests/test_qubo_optimization.py`** (NEW)
   - Exhaustive unit tests: matrix shape, candidate ordering, energy decomposition, ground truth comparison ($N \le 12$), simulated annealing, seed determinism, provenance, API endpoints.
7. **`tests/validate_phase6_qubo.py`** (NEW)
   - Full end-to-end real PDF (`test sample/testreport.pdf`) validation script.
8. **`outputs/phase6_qubo_validation.md`** (NEW)
   - Final validation report.

### Files to Remain Unchanged:
- Neo4j graph store & repositories (`app/graph/*`)
- BGE embedding model & repository (`app/embeddings/*`)
- Persistent FAISS vector store (`app/vectors/*`)
- RRF core logic & ranking formula (`app/rag/hybrid_retriever.py` candidate generator)
- QLoRA student artifacts & model weights

---

## 5. Audit Conclusion

The architecture inspection is complete. Proceeding to implement Step 2 through Step 15.
