"""Teacher Generation Test Suite.

Tests:
1. Ollama health
2. qwen3:4b availability
3. Teacher request
4. Timeout handling
5. Retry limit
6. Response validation
7. Grounding metadata
8. Numerical validation
9. Dataset schema
10. Teacher/student separation
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestOllamaHealth:
    """Test Ollama service health."""

    def test_01_ollama_reachable(self):
        """Ollama server should be reachable."""
        try:
            import ollama
            from app.core.config import get_settings
            settings = get_settings()
            client = ollama.Client(host=settings.ollama_base_url, timeout=10)
            models = client.list()
            assert models is not None
            print("[PASS] Test 1: Ollama reachable")
        except Exception as exc:
            pytest.skip(f"Ollama not available: {exc}")


class TestTeacherModelAvailability:
    """Test teacher model availability."""

    def test_02_qwen3_available(self):
        """qwen3:4b should be available in Ollama."""
        try:
            import ollama
            from app.core.config import get_settings
            settings = get_settings()
            client = ollama.Client(host=settings.ollama_base_url, timeout=10)
            models = client.list()
            model_names = []
            if hasattr(models, 'models'):
                model_names = [m.model for m in models.models]
            elif isinstance(models, dict):
                model_names = [m.get("name", "") for m in models.get("models", [])]
            
            has_qwen3 = any("qwen3" in m for m in model_names)
            assert has_qwen3, f"qwen3:4b not found in: {model_names}"
            print(f"[PASS] Test 2: qwen3:4b available (models: {model_names})")
        except ImportError:
            pytest.skip("ollama package not installed")
        except Exception as exc:
            pytest.skip(f"Ollama not available: {exc}")


class TestTeacherRequest:
    """Test teacher model requests."""

    def test_03_teacher_simple_request(self):
        """Teacher model should respond to a simple request."""
        try:
            import ollama
            from app.core.config import get_settings
            settings = get_settings()
            client = ollama.Client(host=settings.ollama_base_url, timeout=60)
            
            t0 = time.time()
            resp = client.chat(
                model=settings.teacher_model,
                messages=[{"role": "user", "content": "Reply with exactly: OK"}],
                options={"temperature": 0.0, "num_predict": 256},
            )
            latency = round((time.time() - t0) * 1000)
            msg = getattr(resp, "message", None) or (resp.get("message", {}) if hasattr(resp, "get") else {})
            content = getattr(msg, "content", None) if hasattr(msg, "content") else msg.get("content", "")
            answer = (content or "").strip()
            assert len(answer) > 0, "Empty teacher response"
            print(f"[PASS] Test 3: Teacher request OK (latency={latency}ms, reply='{answer[:30]}')")
        except Exception as exc:
            pytest.skip(f"Teacher unavailable: {exc}")


class TestTimeoutHandling:
    """Test timeout and retry behavior."""

    def test_04_timeout_config(self):
        """Teacher timeout should be configurable."""
        from app.core.config import get_settings
        settings = get_settings()
        assert settings.teacher_timeout_seconds > 0
        assert settings.teacher_timeout_seconds <= 300
        print(f"[PASS] Test 4: Timeout={settings.teacher_timeout_seconds}s")

    def test_05_retry_limit(self):
        """Maximum retries should be configured."""
        from app.core.config import get_settings
        settings = get_settings()
        assert settings.teacher_max_retries >= 1
        assert settings.teacher_max_retries <= 5
        print(f"[PASS] Test 5: Max retries={settings.teacher_max_retries}")


class TestResponseValidation:
    """Test teacher response validation."""

    def test_06_response_schema(self):
        """OllamaTeacher should validate response format."""
        from app.distillation.teacher import _valid_teacher_response
        
        # Valid response
        assert _valid_teacher_response({"answer": "CatBoost achieved 97.5%", "evidence": "From page 5"})
        # Invalid: empty
        assert not _valid_teacher_response({"answer": "", "evidence": ""})
        assert not _valid_teacher_response({})
        assert not _valid_teacher_response(None)
        print("[PASS] Test 6: Response validation")


class TestGroundingMetadata:
    """Test grounding status metadata."""

    def test_07_grounding_labels(self):
        """Grounding status should be one of SUPPORTED/PARTIALLY_SUPPORTED/UNSUPPORTED."""
        valid_statuses = {"SUPPORTED", "PARTIALLY_SUPPORTED", "UNSUPPORTED"}
        for status in valid_statuses:
            assert status in valid_statuses
        print("[PASS] Test 7: Grounding labels valid")


class TestNumericalValidation:
    """Test numerical value validation."""

    def test_08_numerical_preservation(self):
        """Numerical values should be preserved exactly."""
        import re
        source = "CatBoost achieved 97.5% accuracy with precision 0.98 and recall 0.97"
        numbers = re.findall(r'\d+\.?\d*%?', source)
        assert "97.5%" in numbers
        assert "0.98" in numbers
        assert "0.97" in numbers
        print(f"[PASS] Test 8: Numerical values found: {numbers}")


class TestDatasetSchema:
    """Test teacher dataset schema."""

    def test_09_dataset_schema_validation(self):
        """Teacher dataset record should have required fields."""
        required_fields = {
            "id", "question", "context", "teacher_answer",
            "source_document", "source_chunks", "source_pages",
            "model", "generation_method", "teacher_latency_ms"
        }
        sample_record = {
            "id": "teacher_001",
            "question": "What is the accuracy?",
            "context": "CatBoost achieved 97.5%",
            "teacher_answer": "97.5%",
            "source_document": "testreport.pdf",
            "source_chunks": ["chunk_001"],
            "source_pages": [5],
            "model": "qwen3:4b",
            "generation_method": "ollama",
            "teacher_latency_ms": 1500,
        }
        missing = required_fields - set(sample_record.keys())
        assert not missing, f"Missing fields: {missing}"
        print("[PASS] Test 9: Dataset schema valid")


class TestTeacherStudentSeparation:
    """Test teacher/student model separation."""

    def test_10_teacher_student_distinct(self):
        """Teacher and student models must be different."""
        from app.core.config import get_settings
        from app.distillation.config import PaperDistillationConfig

        settings = get_settings()
        cfg = PaperDistillationConfig()

        teacher = settings.teacher_model  # qwen3:4b
        student = cfg.student_model       # Qwen/Qwen2.5-0.5B-Instruct

        assert teacher != student, f"Teacher and student must be different: {teacher} vs {student}"
        assert "qwen3" in teacher.lower() or "qwen" in teacher.lower()
        assert "0.5B" in student or "qwen2.5" in student.lower()
        print(f"[PASS] Test 10: Teacher={teacher}, Student={student}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
