# DocLink API Documentation

## Overview
The **DocLink API** is built using FastAPI, offering endpoints for system health verification, graph search, vector embedding status, QUBO optimization, document ingestion, and grounded RAG answer generation.

---

## Endpoint Reference

### 1. Core Health Endpoint
- **URL**: `GET /health`
- **Purpose**: Verify backend operational status.
- **Response**:
```json
{
  "ok": true,
  "status": "healthy",
  "name": "DocLink Document Intelligence Platform",
  "environment": "production"
}
```

---

### 2. Neo4j Graph Health & Status
- **URL**: `GET /api/graph/health`
- **Purpose**: Check Neo4j graph driver connectivity.
- **Response**:
```json
{
  "status": "ready",
  "backend": "neo4j",
  "uri": "bolt://localhost:7687"
}
```

- **URL**: `GET /api/graph/status`
- **Purpose**: Return total node and relationship counts in graph database.

---

### 3. Embedding Status Endpoint
- **URL**: `GET /api/embeddings/status`
- **Purpose**: Check active embedding provider and CUDA state.
- **Response**:
```json
{
  "provider": "sentence_transformers",
  "model": "BAAI/bge-small-en-v1.5",
  "dimension": 384,
  "device": "cuda",
  "normalized": true,
  "status": "ready"
}
```

---

### 4. QUBO Optimization Status & Solver Endpoint
- **URL**: `GET /api/qubo/status`
- **Purpose**: Return QUBO solver availability and default weights.
- **Response**:
```json
{
  "enabled": true,
  "solver": "exact",
  "alpha": 0.5,
  "beta": 0.3,
  "gamma": 0.2
}
```

- **URL**: `POST /api/qubo/optimize`
- **Purpose**: Submit candidate feature vectors for direct QUBO optimization.

---

### 5. QLoRA Student Status Endpoint
- **URL**: `GET /api/student/status`
- **Purpose**: Check QLoRA student LLM availability.
- **Response**:
```json
{
  "available": true,
  "base_model": "Qwen/Qwen2.5-0.5B-Instruct",
  "adapter_path": "outputs/distillation/student",
  "device": "cuda"
}
```

---

### 6. Grounded RAG Answer Endpoint (Primary)
- **URL**: `POST /api/rag/answer`
- **Request Payload**:
```json
{
  "query": "What sensors were used in the IoT architecture?",
  "top_k": 5,
  "qubo_k": 3,
  "enable_qubo": true,
  "max_new_tokens": 256
}
```

- **Response Payload**:
```json
{
  "query": "What sensors were used in the IoT architecture?",
  "answer": "According to [E1] and [E2], the IoT architecture utilized the ESP32 microcontroller, SGP30 gas sensor, and SHT40 temperature/humidity sensor.",
  "citations": ["E1", "E2"],
  "evidence": [
    {
      "evidence_id": "E1",
      "document_id": "testreport.pdf",
      "page_number": 4,
      "text": "Fig. 2. Wiring diagram of ESP32, SGP30 sensor and SHT40 sensor.",
      "qubo_score": -0.4852
    }
  ],
  "retrieval": {
    "vector_candidates": 10,
    "graph_candidates": 0,
    "fused_count": 10
  },
  "qubo": {
    "qubo_enabled": true,
    "solver_type": "exact",
    "total_energy": -0.4852,
    "qubo_optimization_time_ms": 4.58
  },
  "model": {
    "base_model": "Qwen/Qwen2.5-0.5B-Instruct",
    "adapter": "outputs/distillation/student"
  },
  "grounding": {
    "grounding_pass": true,
    "numerical_valid": true,
    "cited_evidence_ids": ["E1", "E2"]
  },
  "total_latency_ms": 9891.04
}
```

- **HTTP Status Codes**:
  - `200 OK`: Successful query execution.
  - `400 Bad Request`: Empty query, query length $>1000$, or $K_{\text{qubo}} > K_{\text{top}}$.
  - `422 Unprocessable Entity`: Invalid JSON schema.
  - `500 Internal Server Error`: Generic internal failure without stack trace disclosure.
