"""Phase 7 Final Grounded RAG Pipeline Engine.

Connects:
FAISS + Neo4j -> RRF Fusion -> QUBO Evidence Selection -> Context Builder -> QLoRA Student -> Grounding Validator
"""
from __future__ import annotations

import time
import logging
from typing import Any, Dict, List, Optional

from ..services.student_service import get_student_service
from .context_builder import build_grounded_context, build_strict_grounded_prompt
from .grounding_validator import validate_grounded_answer
from .hybrid_retriever import HybridRetriever

log = logging.getLogger("gen-transform.rag.grounded_rag")


class GroundedRAGService:
    """Complete Grounded RAG execution service with QUBO evidence selection and QLoRA student generation."""

    def __init__(self, hybrid_retriever: Optional[HybridRetriever] = None) -> None:
        self.hybrid_retriever = hybrid_retriever or HybridRetriever()

    def answer_query(
        self,
        query: str,
        top_k: int = 5,
        qubo_k: int = 3,
        enable_qubo: bool = True,
        max_new_tokens: int = 256,
    ) -> Dict[str, Any]:
        """Execute complete Grounded RAG pipeline for query.

        Steps:
        1. Retrieve hybrid candidates & apply RRF + QUBO selection
        2. Format evidence into structured [E1], [E2] context
        3. Build strict anti-hallucination prompt
        4. Execute QLoRA student model inference
        5. Perform deterministic grounding & citation validation
        """
        t_total_start = time.time()
        clean_query = (query or "").strip()

        # Step 1: Execute Hybrid Retrieval + QUBO Evidence Selection
        t_ret_start = time.time()
        # Retrieve target qubo_k candidates selected by QUBO
        selected_candidates, metrics = self.hybrid_retriever.retrieve(
            query=clean_query,
            top_k=qubo_k,
            enable_qubo=enable_qubo,
        )
        retrieval_ms = round((time.time() - t_ret_start) * 1000, 2)

        # Step 2: Context Builder
        t_ctx_start = time.time()
        formatted_context, evidence_manifest, citations_map = build_grounded_context(selected_candidates)
        context_build_ms = round((time.time() - t_ctx_start) * 1000, 2)

        # Step 3: Prompt Construction
        grounded_prompt = build_strict_grounded_prompt(clean_query, formatted_context)

        # Step 4: QLoRA Student Inference
        t_gen_start = time.time()
        student_service = get_student_service()
        student_res = student_service.generate_grounded_answer(
            prompt=grounded_prompt,
            max_new_tokens=max_new_tokens,
        )
        generation_ms = round((time.time() - t_gen_start) * 1000, 2)

        # Step 5: Grounding & Citation Validation
        t_val_start = time.time()
        grounding_res = validate_grounded_answer(
            answer=student_res["text"],
            evidence_manifest=evidence_manifest,
            citations_map=citations_map,
        )
        validation_ms = round((time.time() - t_val_start) * 1000, 2)

        total_ms = round((time.time() - t_total_start) * 1000, 2)

        return {
            "query": clean_query,
            "answer": student_res["text"],
            "citations": grounding_res["cited_evidence_ids"],
            "evidence": evidence_manifest,
            "retrieval": {
                "vector_candidates": metrics.get("vector_candidates", 0),
                "graph_candidates": metrics.get("graph_candidates", 0),
                "fused_count": metrics.get("fused_count", 0),
                "embedding_time_ms": metrics.get("embedding_time", 0.0),
                "faiss_search_time_ms": metrics.get("faiss_search_time", 0.0),
                "neo4j_search_time_ms": metrics.get("neo4j_search_time", 0.0),
                "fusion_time_ms": metrics.get("fusion_time", 0.0),
                "total_retrieval_ms": retrieval_ms,
            },
            "qubo": {
                "qubo_enabled": metrics.get("qubo_enabled", True),
                "qubo_ms": metrics.get("qubo_optimization_time_ms", 0.0),
                "solver_type": metrics.get("qubo_solver_type", "exact"),
                "total_energy": metrics.get("qubo_total_energy", 0.0),
                "objective_breakdown": metrics.get("qubo_objective_breakdown", {}),
            },
            "model": {
                "base_model": student_res["base_model"],
                "adapter": student_res["adapter_path"],
                "device": student_res["device"],
                "generation_ms": generation_ms,
                "tokens_generated": student_res.get("tokens_generated", 0),
            },
            "grounding": grounding_res,
            "latency_breakdown_ms": {
                "retrieval_ms": retrieval_ms,
                "qubo_ms": metrics.get("qubo_optimization_time_ms", 0.0),
                "context_build_ms": context_build_ms,
                "student_generation_ms": generation_ms,
                "validation_ms": validation_ms,
                "total_ms": total_ms,
            },
        }


_GROUNDED_RAG_SERVICE_INSTANCE: Optional[GroundedRAGService] = None


def get_grounded_rag_service() -> GroundedRAGService:
    """Return singleton instance of GroundedRAGService."""
    global _GROUNDED_RAG_SERVICE_INSTANCE
    if _GROUNDED_RAG_SERVICE_INSTANCE is None:
        _GROUNDED_RAG_SERVICE_INSTANCE = GroundedRAGService()
    return _GROUNDED_RAG_SERVICE_INSTANCE


def reset_grounded_rag_service() -> None:
    """Reset singleton instance for testing."""
    global _GROUNDED_RAG_SERVICE_INSTANCE
    _GROUNDED_RAG_SERVICE_INSTANCE = None


__all__ = [
    "GroundedRAGService",
    "get_grounded_rag_service",
    "reset_grounded_rag_service",
]
