# Phase 7 — QLoRA Student Architecture Audit & Inspection

**Date**: 2026-09-26  
**Project**: Gen-Transform-AI  
**Phase**: Phase 7 — Final Grounded RAG + QLoRA Student Integration  

---

## 1. Student Model & PEFT Adapter Inspection

A thorough inspection of the fine-tuned student model directory [`Backend/outputs/distillation/student`](file:///c:/Users/premk/OneDrive/Documents/gen-transform-ai/Backend/outputs/distillation/student) confirms that the QLoRA adapter is intact, verified, and loadable.

### 1.1 Verified Adapter Metadata:
- **Base Model Path**: `Qwen/Qwen2.5-0.5B-Instruct`
- **Adapter Directory**: `Backend/outputs/distillation/student`
- **Adapter Type**: `LORA` (PEFT version `0.21.0`)
- **LoRA Hyperparameters**:
  - Rank ($r$): `4`
  - LoRA Alpha ($\alpha$): `8`
  - LoRA Dropout: `0.05`
  - Target Modules: `q_proj`, `k_proj`, `v_proj`, `o_proj`
  - Task Type: `CAUSAL_LM`
- **Adapter Weights File**: `adapter_model.safetensors` (2.18 MB)
- **Tokenizer Files**: `tokenizer.json` (11.4 MB), `tokenizer_config.json` (724 B)

---

## 2. Infrastructure & Hardware Constraints

- **Available GPU Hardware**: NVIDIA RTX 3050 Laptop GPU (4 GB VRAM)
- **PyTorch Acceleration**: CUDA enabled (`torch.cuda.is_available() == True`)
- **Memory Safety & Strategy**:
  - Base model size: 0.5B parameters (~1.0 GB VRAM in FP16 / FP32)
  - LoRA adapter overhead: ~2.2 MB
  - Inference mode: `model.eval()`, `torch.no_grad()`, `inference_mode()`
  - Single static model loading instance (singleton pattern) to prevent VRAM allocation spikes.
  - Device strategy: `cuda` if available; graceful CPU fallback if VRAM allocation fails. No silent fake model fallbacks.

---

## 3. Integration Pipeline Architecture

The complete end-to-end grounded RAG pipeline is structured as follows:

```text
User Query
   ↓
Query Embedding (BAAI/bge-small-en-v1.5)
   ↓
FAISS Retrieval (Persistent IndexFlatIP)
   ↓
Neo4j Graph Retrieval (Parameterized Cypher)
   ↓
RRF Fusion (Reciprocal Rank Fusion k=60)
   ↓
QUBO Evidence Selection (Exact / Simulated Annealing min_x x^T Q x)
   ↓
Context Builder (Structured [E1], [E2]... with document_id, page_number, chunk_id)
   ↓
Strict Grounded Prompt Construction (Anti-hallucination rules)
   ↓
QLoRA Student (Qwen2.5-0.5B-Instruct + PEFT Adapter)
   ↓
Grounding & Citation Validator (Deterministic citation & numerical integrity check)
   ↓
Final Response (Answer + Citations + Evidence + Full Provenance Metrics)
```

---

## 4. Teacher Status Notice

- **Teacher Qwen3 Status**: **BLOCKED** (Local Ollama service `qwen3:4b` instance failed GPU initialization).
- **Rule Verification**: Per Phase 7 requirements, Qwen3 teacher generation is strictly **NOT** a dependency for Phase 7 grounded RAG execution. The fine-tuned QLoRA student adapter is loaded directly.

---

## 5. Planned Code Changes & File Impact

### Files to be Created:
1. **`Backend/app/services/student_service.py`**
   - Singleton service loading `Qwen/Qwen2.5-0.5B-Instruct` base model and `outputs/distillation/student` PEFT adapter. Provides `generate_grounded_answer()`.
2. **`Backend/app/rag/grounded_rag.py`**
   - End-to-end RAG orchestrator connecting FAISS + Neo4j + RRF + QUBO + Context Builder + Student Service + Grounding Validator.
3. **`Backend/app/rag/grounding_validator.py`**
   - Deterministic grounding and citation validation engine.
4. **`Backend/app/api/routes/student.py`**
   - Student status endpoint `GET /api/student/status`.
5. **`Backend/tests/test_phase7_grounded_rag.py`**
   - Comprehensive test suite for Phase 7 (18 test cases).
6. **`Backend/tests/validate_phase7_rag.py`**
   - Real PDF end-to-end benchmark script against `test sample/testreport.pdf`.
7. **`outputs/phase7_final_rag_validation.md`**
   - Final Phase 7 validation report.

### Files to be Modified:
1. **`Backend/app/api/routes/rag.py`**
   - Add `POST /api/rag/answer` and `GET /api/rag/answer/status`.
2. **`Backend/app/main.py`**
   - Include student router.

---

## 6. Audit Conclusion

The architecture audit is complete. Proceeding with implementation of Steps 2 through 18.
