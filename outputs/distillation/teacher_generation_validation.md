# Part B — Real Teacher Qwen3 Generation Validation Report

**Date**: 2026-09-25  
**Project**: Gen-Transform-AI  
**Status**: **TEACHER QWEN3 BLOCKED (TIMEOUT / REASONING TOKEN EXHAUSTION)**  

---

## 1. Executive Summary

This report documents the validation of the **Real Teacher Qwen3 Generation Pipeline** via the local Ollama API (`http://127.0.0.1:11434`) using `qwen3:4b`.

In strict adherence to the project's verification and labeling policies:
- **No Mock / Fabricated Outputs**: Responses are never mocked or artificially simulated.
- **No Label Conflation**: The existing 200-record grounded reference dataset is strictly preserved as `grounded` and **never** mislabeled as teacher-generated.
- **Independent Status Verification**: Teacher generation status is evaluated independently from student QLoRA training. Because `qwen3:4b` is a reasoning model that consumes excessive chain-of-thought tokens on long research-paper contexts, teacher generation timed out during generation.
- **Strict Final Status**: `TEACHER QWEN3: BLOCKED`, `TEACHER DATASET: NOT GENERATED`, `QLORA STUDENT: ALREADY TRAINED`.

---

## 2. Infrastructure & Model Inspection

| Component | Setting / Value | Actual State |
| :--- | :--- | :---: |
| **Ollama Service** | `http://127.0.0.1:11434` | **REACHABLE / RUNNING** |
| **Available Models** | `ollama list` | `qwen3:4b` (2.5 GB), `gemma3:4b` (3.3 GB) |
| **Configured Teacher** | `TEACHER_MODEL=qwen3:4b` | **PRESENT** |
| **Configured Timeout** | `TEACHER_TIMEOUT_SECONDS=180` | **CONFIGURED** |
| **Max Retry Limit** | `TEACHER_MAX_RETRIES=2` | **CONFIGURED** |
| **Teacher Architecture** | `Qwen3 4B` (Reasoning / Thinking Model) | **VERIFIED** |
| **Student Architecture** | `Qwen/Qwen2.5-0.5B-Instruct` (QLoRA) | **SEPARATED** |
| **Student Adapter** | `Backend/outputs/distillation/student` | **ALREADY TRAINED** |

---

## 3. Teacher Model Health & Probe Analysis

### Step 16: Ollama Model Verification
- `ollama list` output confirmed `qwen3:4b` (ID: `359d7dd4bcda`, Size: 2.5 GB).

### Step 17: Teacher Health Check
- Simple prompt test (`"Reply with exactly: OK"`):
  - **Latency**: 1,248 ms
  - **HTTP Status**: 200 OK
  - **Response**: `OK` (Passed in `tests/test_teacher_generation.py::test_03_teacher_simple_request`)

### Step 18: Teacher Probe on Real PDF Context (`test sample/testreport.pdf`)
When evaluated on research-paper context (4,000 characters from `testreport.pdf`), `qwen3:4b` operates as a reasoning model with an internal chain-of-thought buffer (`thinking`).
- **Probe Question 1**: *"What machine learning algorithms were evaluated in the study?"*
  - **Observed Behavior**: The model expended its generation tokens entirely on reasoning (`<think>...`), hitting the token limit (`done_reason: 'length'`) before generating structured JSON output. Latency: 29.8s. Empty parsed answer.
- **Probe Question 2**: *"What sensors were used in the IoT system?"*
  - **Observed Behavior**: Reasoning token exhaustion. Latency: 24.8s. Empty parsed answer.
- **Probe Question 3**: *"What CatBoost performance values are reported?"*
  - **Observed Behavior**: Reasoning token exhaustion / timeout on long context. Latency: 25.7s. Empty parsed answer.
- **Probe Conclusion**: Less than 2/3 probe questions succeeded.
  - Per Rule 19 & 20: Teacher generation is marked **BLOCKED**. No 200-record dataset generation was attempted.

---

## 4. Distillation Dataset Separation & Preservation

### Rule 24 & 25 Verification
- **Grounded Reference Dataset**:
  - Path: `outputs/distillation/teacher_dataset.jsonl` / `outputs/distillation/grounded_dataset.jsonl`
  - Size: 130,850 bytes (200 grounded reference records)
  - Label: `teacher_generated_dataset = false` (Preserved intact; NOT overwritten or deleted).
- **Teacher-Generated Dataset**:
  - Status: **NOT GENERATED** (`teacher_dataset_qwen3.jsonl` not generated due to teacher blockage).
- **Student Dataset Selector**:
  - `DATASET_SOURCE=grounded` (Active configuration in `.env`).
  - Allows the existing QLoRA student adapter to use the validated grounded dataset without interruption.

---

## 5. Test Suite Verification

### `pytest tests/test_teacher_generation.py -v`
```text
tests/test_teacher_generation.py::TestOllamaHealth::test_01_ollama_reachable PASSED             [ 10%]
tests/test_teacher_generation.py::TestTeacherModelAvailability::test_02_qwen3_available PASSED [ 20%]
tests/test_teacher_generation.py::TestTeacherRequest::test_03_teacher_simple_request PASSED   [ 30%]
tests/test_teacher_generation.py::TestTimeoutHandling::test_04_timeout_config PASSED           [ 40%]
tests/test_teacher_generation.py::TestTimeoutHandling::test_05_retry_limit PASSED              [ 50%]
tests/test_teacher_generation.py::TestResponseValidation::test_06_response_schema PASSED       [ 60%]
tests/test_teacher_generation.py::TestGroundingMetadata::test_07_grounding_labels PASSED       [ 70%]
tests/test_teacher_generation.py::TestNumericalValidation::test_08_numerical_preservation PASSED [ 80%]
tests/test_teacher_generation.py::TestDatasetSchema::test_09_dataset_schema_validation PASSED [ 90%]
tests/test_teacher_generation.py::TestTeacherStudentSeparation::test_10_teacher_student_distinct PASSED [100%]

============================= 10 passed in 13.73s =============================
```

---

## 6. Strict Final Status Matrix

```text
============================================================
FINAL STATUS REPORT
============================================================

  PHASE 5:           COMPLETE
  TEACHER QWEN3:     BLOCKED
  TEACHER DATASET:   NOT GENERATED
  QLORA STUDENT:     ALREADY TRAINED

============================================================
```
