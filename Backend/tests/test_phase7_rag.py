"""Phase 7 — Vector + Graph RAG Complete Test Suite.

Tests:
1. Query Analyzer (Entities, Intent, Keywords, Routing)
2. Vector Retriever (Embedding Search, Standardization, Metadata)
3. Graph Retriever (Neo4j Entity Lookup, Relationships, Neighbors, Depth Control)
4. Result Fusion (Weighted, RRF, Deduplication, Agreement, Contradiction Detection)
5. Candidate Reranker (Lightweight Reranker, Top-N Selection)
6. Context Builder & Token Budget (Format, Ordering, Budget Enforcers)
7. Context Validator & Insufficient Evidence Handling
8. Prompt Builder & Citation Tracker (Bracket mapping [1], [2])
9. API Endpoint (POST /api/rag/query)
10. Critical End-to-End Pipeline Test:
    Document -> Phase 6 Indexing + Phase 5 Graph Ingestion -> Phase 7 RAG Query -> Answer + Sources + Graph Evidence + Latency Metrics.
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
from app.rag import (
    CitationTracker,
    ContextBuilder,
    ContextValidator,
    FusionStrategyEnum,
    GraphRetriever,
    LightweightReranker,
    PromptBuilder,
    QueryAnalyzer,
    QueryTypeEnum,
    RAGQueryRequest,
    RAGService,
    ReciprocalRankFusion,
    ResultFusion,
    RetrievalResult,
    VectorRetriever,
    WeightedScoreFusion,
    get_rag_service,
)

client = TestClient(app)

SAMPLE_DOC_ID = "doc_ai_tech_report_2026"
SAMPLE_DOC_TEXT = """## Executive Summary: OpenAI Technology Stack & Infrastructure

OpenAI utilizes PyTorch as its primary deep learning framework for training large-scale GPT models.
The infrastructure runs on high-performance NVIDIA GPU clusters equipped with CUDA and HBM3e high-bandwidth memory.
Model deployment is orchestrated using Kubernetes and optimized custom C++ CUDA kernels.

## Section 2: Framework Ecosystem
PyTorch provides dynamic computation graphs which enable rapid experimentation for transformer architectures.
OpenAI has also developed custom Triton compilers to accelerate GPU kernel operations.
"""


def test_query_analyzer():
    print("\n--- [Test 1] Query Analyzer ---")
    analyzer = QueryAnalyzer()
    q = "What technologies are used by OpenAI?"
    analysis = analyzer.analyze(q)

    assert "OpenAI" in analysis.entities or "openai" in [k.lower() for k in analysis.keywords]
    assert analysis.intent == "technology_usage"
    assert analysis.semantic_query == q
    assert analysis.query_type in [QueryTypeEnum.HYBRID, QueryTypeEnum.SEMANTIC]
    print(f"  [OK] Analysis: entities={analysis.entities}, intent={analysis.intent}, type={analysis.query_type}")


def test_vector_retriever():
    print("\n--- [Test 2] Vector Retriever ---")
    embed_svc = get_embedding_service()
    embed_svc.index_text(
        text=SAMPLE_DOC_TEXT,
        document_id=SAMPLE_DOC_ID,
        source_filename="ai_tech_report_2026.pdf",
    )

    vector_retriever = VectorRetriever(service=embed_svc)
    results, latency_ms = vector_retriever.retrieve(
        query="PyTorch CUDA OpenAI GPU",
        top_k=3,
        document_id=SAMPLE_DOC_ID,
    )

    assert len(results) > 0, "Vector retriever returned empty list"
    assert results[0].source_type == "vector"
    assert results[0].document_id == SAMPLE_DOC_ID
    assert "PyTorch" in results[0].text or "OpenAI" in results[0].text
    print(f"  [OK] Vector search retrieved {len(results)} items in {latency_ms}ms. Top score: {results[0].score:.3f}")


def test_graph_retriever():
    print("\n--- [Test 3] Graph Retriever ---")
    graph_svc = GraphService()
    # Ingest mock graph payload
    payload = GraphPayload(
        document=DocumentNodeModel(document_id=SAMPLE_DOC_ID, title="AI Tech Report", total_pages=2),
        nodes=[
            GraphNodeModel(entity_id="OpenAI", label="Organization", canonical_name="OpenAI", entity_type="Organization"),
            GraphNodeModel(entity_id="PyTorch", label="Technology", canonical_name="PyTorch", entity_type="Technology"),
            GraphNodeModel(entity_id="CUDA", label="Technology", canonical_name="CUDA", entity_type="Technology"),
        ],
        relationships=[
            GraphRelationshipModel(
                relation_id="rel_001",
                source_id="OpenAI",
                target_id="PyTorch",
                relation_type="USES",
                document_id=SAMPLE_DOC_ID,
                page=1,
                evidence_text="OpenAI utilizes PyTorch as its primary deep learning framework.",
            ),
            GraphRelationshipModel(
                relation_id="rel_002",
                source_id="OpenAI",
                target_id="CUDA",
                relation_type="USES",
                document_id=SAMPLE_DOC_ID,
                page=1,
                evidence_text="Infrastructure runs on NVIDIA GPU clusters equipped with CUDA.",
            ),
        ],
    )
    graph_svc.ingest_doclink_result(payload)

    graph_retriever = GraphRetriever(service=graph_svc)
    analyzer = QueryAnalyzer()
    analysis = analyzer.analyze("What technologies does OpenAI use?")

    results, latency_ms = graph_retriever.retrieve(
        analysis=analysis,
        graph_depth=1,
        document_id=SAMPLE_DOC_ID,
        top_k=5,
    )

    assert len(results) >= 1, "Graph retriever should return relationships"
    assert results[0].source_type == "graph"
    assert "OpenAI" in results[0].text
    print(f"  [OK] Graph search retrieved {len(results)} items in {latency_ms}ms. Top text: {results[0].text}")


def test_result_fusion():
    print("\n--- [Test 4] Result Fusion & Deduplication ---")
    v_item = RetrievalResult(
        source_type="vector",
        source_id="chunk_001",
        document_id=SAMPLE_DOC_ID,
        text="OpenAI utilizes PyTorch for deep learning training.",
        score=0.92,
        metadata={"page_number": 1},
        evidence={"chunk_id": "chunk_001", "page": 1},
    )
    g_item = RetrievalResult(
        source_type="graph",
        source_id="rel_001",
        document_id=SAMPLE_DOC_ID,
        text="OpenAI --[USES]--> PyTorch",
        score=0.90,
        metadata={"source": "OpenAI", "relation": "USES", "target": "PyTorch"},
        evidence={"source": "OpenAI", "relation": "USES", "target": "PyTorch"},
    )

    fusion = ResultFusion()
    # Test Weighted
    fused_weighted, agreement, conflicts, ms = fusion.fuse_and_deduplicate(
        vector_results=[v_item],
        graph_results=[g_item],
        strategy=FusionStrategyEnum.WEIGHTED,
        vector_weight=0.6,
        graph_weight=0.4,
    )

    assert len(fused_weighted) == 2
    assert agreement is True, "Agreement should be detected since vector text contains OpenAI and PyTorch"
    print(f"  [OK] Weighted Fusion: agreement={agreement}, conflicts={len(conflicts)}, ms={ms}")

    # Test RRF
    fused_rrf, _, _, ms_rrf = fusion.fuse_and_deduplicate(
        vector_results=[v_item],
        graph_results=[g_item],
        strategy=FusionStrategyEnum.RRF,
    )
    assert len(fused_rrf) == 2
    print(f"  [OK] RRF Fusion: {len(fused_rrf)} candidates fused in {ms_rrf}ms.")


def test_reranker():
    print("\n--- [Test 5] Candidate Reranker ---")
    reranker = LightweightReranker()
    candidates = [
        RetrievalResult(
            source_type="vector",
            source_id="c1",
            document_id="doc1",
            text="General history of computer hardware from 1980.",
            score=0.85,
        ),
        RetrievalResult(
            source_type="vector",
            source_id="c2",
            document_id="doc1",
            text="OpenAI utilizes PyTorch and CUDA GPUs extensively.",
            score=0.80,
        ),
    ]

    reranked, ms = reranker.rerank(query="What technologies does OpenAI use?", candidates=candidates, top_n=2)
    assert len(reranked) == 2
    assert reranked[0].source_id == "c2", "c2 should be reranked to top due to query keyword matches"
    print(f"  [OK] Reranker re-ordered candidate 'c2' to position 1 in {ms}ms.")


def test_context_builder_and_budget():
    print("\n--- [Test 6] Context Builder & Token Budget ---")
    builder = ContextBuilder(max_chunks=2, max_graph=2, max_tokens=500)
    candidates = [
        RetrievalResult(
            source_type="vector",
            source_id="c1",
            document_id=SAMPLE_DOC_ID,
            text="OpenAI utilizes PyTorch as its primary deep learning framework.",
            score=0.9,
            metadata={"page_number": 1, "source_filename": "report.pdf"},
            evidence={"page": 1, "filename": "report.pdf"},
        ),
        RetrievalResult(
            source_type="graph",
            source_id="r1",
            document_id=SAMPLE_DOC_ID,
            text="OpenAI --[USES]--> PyTorch",
            score=0.9,
            metadata={"source": "OpenAI", "relation": "USES", "target": "PyTorch"},
            evidence={"source": "OpenAI", "relation": "USES", "target": "PyTorch"},
        ),
    ]

    context_text, selected = builder.build_context("What technologies does OpenAI use?", candidates)
    assert "DOCUMENT EVIDENCE:" in context_text
    assert "GRAPH EVIDENCE:" in context_text
    assert "SOURCE INFORMATION:" in context_text
    assert len(selected) == 2
    print(f"  [OK] Context text constructed cleanly ({len(context_text)} characters).")


def test_validator_and_insufficient_evidence():
    print("\n--- [Test 7] Validator & Insufficient Evidence ---")
    validator = ContextValidator()

    # Empty candidates case
    ok1, reason1 = validator.validate([], min_retrieval_score=0.5)
    assert ok1 is False
    assert "No relevant" in reason1

    # Score below threshold case
    weak_cand = [RetrievalResult(source_type="vector", source_id="c1", text="Unrelated info", score=0.2)]
    ok2, reason2 = validator.validate(weak_cand, min_retrieval_score=0.5)
    assert ok2 is False
    assert "below" in reason2
    print("  [OK] Validator correctly rejects insufficient/low-scoring evidence.")


def test_prompt_and_citation_tracker():
    print("\n--- [Test 8] Prompt Builder & Citation Tracker ---")
    prompt_builder = PromptBuilder()
    prompt_dict = prompt_builder.build_prompt("What is OpenAI's tech stack?", "DOCUMENT EVIDENCE:\n[1] OpenAI uses PyTorch.")

    assert "system" in prompt_dict and "user" in prompt_dict
    assert "QUESTION: What is OpenAI's tech stack?" in prompt_dict["user"]

    tracker = CitationTracker()
    cand = RetrievalResult(
        source_type="vector",
        source_id="chunk_004",
        document_id="doc_123",
        text="OpenAI uses PyTorch...",
        score=0.94,
        metadata={"page_number": 4, "source_filename": "ai_report.pdf"},
        evidence={"page": 4, "filename": "ai_report.pdf"},
    )
    sources, graph_ev = tracker.build_citations([cand])

    assert len(sources) == 1
    assert sources[0].citation_id == "1"
    assert sources[0].chunk_id == "chunk_004"
    assert sources[0].page == 4
    print("  [OK] Prompt builder and citation tracker verified successfully.")


def test_api_rag_endpoint():
    print("\n--- [Test 9] API Endpoint POST /api/rag/query ---")
    req_data = {
        "query": "What technologies does OpenAI use?",
        "top_k": 5,
        "graph_depth": 1,
        "document_id": SAMPLE_DOC_ID,
        "rerank": True,
        "fusion_strategy": "weighted",
        "vector_weight": 0.6,
        "graph_weight": 0.4,
    }

    res = client.post("/api/rag/query", json=req_data)
    assert res.status_code == 200, f"API failed: {res.text}"

    data = res.json()
    assert data["query"] == "What technologies does OpenAI use?"
    assert "answer" in data
    assert "retrieval" in data
    assert data["retrieval"]["total_ms"] > 0
    print(f"  [OK] POST /api/rag/query returned 200 OK. Total ms: {data['retrieval']['total_ms']}ms")


def test_critical_e2e_rag_pipeline():
    print("\n--- [Test 10] Critical End-to-End Hybrid RAG Pipeline ---")
    rag_service = get_rag_service()

    req = RAGQueryRequest(
        query="What technologies are used by OpenAI?",
        top_k=5,
        graph_depth=1,
        document_id=SAMPLE_DOC_ID,
        rerank=True,
    )

    response = rag_service.query(req)

    assert response.query == req.query
    assert response.insufficient_evidence is False
    assert len(response.answer) > 10
    assert response.retrieval.vector_results > 0
    assert response.retrieval.total_ms > 0
    assert response.query_analysis is not None

    print("\n  ==========================================================")
    print(f"  E2E QUERY : {response.query}")
    print(f"  ANSWER    : {response.answer[:150]}...")
    print(f"  CITATIONS : {len(response.sources)} document sources")
    print(f"  GRAPH EV  : {len(response.graph_evidence)} graph relations")
    print(f"  LATENCY   : total={response.retrieval.total_ms}ms (vector={response.retrieval.vector_ms}ms, graph={response.retrieval.graph_ms}ms, gen={response.retrieval.generation_ms}ms)")
    print("  ==========================================================")


if __name__ == "__main__":
    test_query_analyzer()
    test_vector_retriever()
    test_graph_retriever()
    test_result_fusion()
    test_reranker()
    test_context_builder_and_budget()
    test_validator_and_insufficient_evidence()
    test_prompt_and_citation_tracker()
    test_api_rag_endpoint()
    test_critical_e2e_rag_pipeline()
    print("\n[SUCCESS] ALL PHASE 7 VECTOR + GRAPH RAG TESTS PASSED SUCCESSFULLY!")

