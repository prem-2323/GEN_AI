"""Phase 7 — Grounded RAG + QLoRA Student Test Suite.

Verifies:
1. Student adapter path exists
2. Adapter configuration valid
3. Student service loads
4. Student inference works
5. Context builder
6. Evidence IDs
7. Citation preservation
8. QUBO -> context integration
9. Grounded prompt construction
10. Grounding validator
11. Numerical validation
12. API /api/rag/answer
13. API status endpoints
14. Missing evidence behavior
15. Invalid citation detection
16. No-evidence answer behavior
17. Real PDF integration
18. End-to-end RAG
"""
from __future__ import annotations

import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.rag.context_builder import build_grounded_context, build_strict_grounded_prompt
from app.rag.grounding_validator import validate_grounded_answer
from app.rag.grounded_rag import GroundedRAGService, get_grounded_rag_service
from app.services.student_service import StudentInferenceService, get_student_service

client = TestClient(app)

STUDENT_ADAPTER_DIR = Path(__file__).resolve().parent.parent / "outputs" / "distillation" / "student"


class TestPhase7StudentAndRAG:

    def test_01_student_adapter_path_exists(self):
        assert STUDENT_ADAPTER_DIR.exists()
        assert (STUDENT_ADAPTER_DIR / "adapter_config.json").exists()

    def test_02_adapter_configuration_valid(self):
        import json
        with open(STUDENT_ADAPTER_DIR / "adapter_config.json", "r") as f:
            cfg = json.load(f)
        assert cfg.get("base_model_name_or_path") == "Qwen/Qwen2.5-0.5B-Instruct"
        assert cfg.get("peft_type") == "LORA"

    def test_03_student_service_loads(self):
        service = get_student_service()
        assert service is not None
        status = service.get_status()
        assert status["available"] is True
        assert status["base_model"] == "Qwen/Qwen2.5-0.5B-Instruct"

    def test_04_student_inference_works(self):
        service = get_student_service()
        res = service.generate_grounded_answer("What is CatBoost?", max_new_tokens=32)
        assert "text" in res
        assert isinstance(res["text"], str)
        assert "latency_ms" in res

    def test_05_context_builder_formatting(self):
        candidates = [
            {"document_id": "doc1", "chunk_id": "chunk_01", "page_number": 2, "text": "CatBoost accuracy is 97.5%.", "source": "vector", "score": 0.95},
            {"document_id": "doc1", "chunk_id": "chunk_02", "page_number": 5, "text": "ESP32 IoT sensor node.", "source": "graph", "score": 0.85},
        ]
        context_str, manifest, citations_map = build_grounded_context(candidates)
        assert "[E1]" in context_str
        assert "[E2]" in context_str
        assert "CatBoost accuracy is 97.5%." in context_str
        assert len(manifest) == 2
        assert "E1" in citations_map

    def test_06_evidence_ids(self):
        candidates = [{"chunk_id": "c1", "text": "test evidence text"}]
        _, manifest, citations = build_grounded_context(candidates)
        assert manifest[0]["evidence_id"] == "E1"
        assert citations["E1"]["text"] == "test evidence text"

    def test_07_citation_preservation(self):
        candidates = [{"document_id": "pdf_test", "page_number": 8, "text": "CatBoost model performance."}]
        _, manifest, _ = build_grounded_context(candidates)
        assert manifest[0]["document_id"] == "pdf_test"
        assert manifest[0]["page_number"] == 8

    def test_08_qubo_to_context_integration(self):
        from app.rag.hybrid_retriever import HybridRetriever
        retriever = HybridRetriever()
        selected, metrics = retriever.retrieve(query="CatBoost model evaluation", top_k=3, enable_qubo=True)
        context_str, manifest, _ = build_grounded_context(selected)

        assert metrics["qubo_enabled"] is True
        assert len(manifest) <= 3

    def test_09_grounded_prompt_construction(self):
        prompt = build_strict_grounded_prompt(question="What is X?", formatted_context="[E1]\nText: X is Y.")
        assert "RULES:" in prompt
        assert "[E1]" in prompt
        assert "QUESTION: What is X?" in prompt

    def test_10_grounding_validator(self):
        evidence = [{"text": "CatBoost accuracy is 97.5%."}]
        citations_map = {"E1": evidence[0]}

        # Valid answer
        res_valid = validate_grounded_answer("According to [E1], CatBoost accuracy is 97.5%.", evidence, citations_map)
        assert res_valid["grounding_pass"] is True
        assert res_valid["cited_evidence_ids"] == ["E1"]

    def test_11_numerical_validation(self):
        evidence = [{"text": "The ESP32 microcontroller collects sensor data at 97.5% accuracy."}]
        citations_map = {"E1": evidence[0]}

        # Valid numbers
        res_ok = validate_grounded_answer("The accuracy is 97.5% in [E1].", evidence, citations_map)
        assert res_ok["numerical_valid"] is True

        # Unsupported numbers
        res_bad = validate_grounded_answer("The accuracy is 99.9% in [E1].", evidence, citations_map)
        assert res_bad["numerical_valid"] is False
        assert "99.9" in res_bad["unsupported_numbers"]


    def test_12_api_rag_answer_endpoint(self):
        payload = {
            "query": "What sensors were used in the IoT system?",
            "top_k": 5,
            "qubo_k": 3,
            "enable_qubo": True,
            "max_new_tokens": 64,
        }
        resp = client.post("/api/rag/answer", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "citations" in data
        assert "grounding" in data
        assert "qubo" in data

    def test_13_api_status_endpoints(self):
        resp_student = client.get("/api/student/status")
        assert resp_student.status_code == 200
        assert resp_student.json()["available"] is True

        resp_rag = client.get("/api/rag/answer/status")
        assert resp_rag.status_code == 200
        assert resp_rag.json()["status"] == "ready"

    def test_14_missing_evidence_behavior(self):
        context_str, manifest, citations = build_grounded_context([])
        res = validate_grounded_answer("The supplied evidence is insufficient to answer this query.", manifest, citations)
        assert res["grounding_pass"] is True

    def test_15_invalid_citation_detection(self):
        evidence = [{"text": "Test evidence"}]
        citations_map = {"E1": evidence[0]}
        res = validate_grounded_answer("As stated in [E99], data is valid.", evidence, citations_map)
        assert res["citations_valid"] is False
        assert "E99" in res["invalid_citations"]

    def test_16_no_evidence_answer_behavior(self):
        service = GroundedRAGService()
        # Query on query outside document
        res = service.answer_query(query="xyz_non_existent_topic_query_9999", top_k=2, qubo_k=2)
        assert "answer" in res
        assert "grounding" in res

    def test_17_real_pdf_integration(self):
        service = GroundedRAGService()
        res = service.answer_query(query="What machine learning algorithms were evaluated?", top_k=5, qubo_k=3)
        assert len(res["evidence"]) > 0
        assert res["qubo"]["qubo_enabled"] is True

    def test_18_end_to_end_rag(self):
        service = GroundedRAGService()
        res = service.answer_query(query="How did CatBoost perform?", top_k=5, qubo_k=3)
        assert res["query"] == "How did CatBoost perform?"
        assert isinstance(res["answer"], str)
        assert "grounding_pass" in res["grounding"]
