# Complete 16-Step System Data Flow Specification

## Executive Overview
This document details the step-by-step data transformation lifecycle inside the **DocLink Grounded RAG Platform**, tracing raw PDF document ingestion to final grounded UI citation rendering.

---

## 16-Step End-to-End Data Flow

```
 1. Document Upload
        │
 2. Text & Layout Extraction (PyMuPDF)
        │
 3. Context-Preserving Semantic Chunking
        │
 4. Entity & Fact Tuple Extraction (DocLink)
        │
 5. Neo4j Graph Indexing (Parameterized Cypher MERGE)
        │
 6. BGE Vector Embedding Generation (384-dim CUDA)
        │
 7. FAISS Vector Store Indexing (IndexFlatIP)
        │
 8. User Query Vector Embedding
        │
 9. FAISS Dense Vector Similarity Retrieval
        │
10. Neo4j Graph Relationship & Neighborhood Retrieval
        │
11. Reciprocal Rank Fusion (RRF k=60) & Deduplication
        │
12. QUBO Binary Matrix Formulation & Optimization
        │
13. Grounded Context Builder ([E1], [E2] Formatting)
        │
14. QLoRA Student LLM Inference (Qwen2.5-0.5B-Instruct)
        │
15. Grounding & Numerical Fact Verification
        │
16. Grounded Answer + Source Citation UI Rendering
```

---

## Detailed Step Description

1. **Document Upload**: User uploads PDF via React UI (`POST /api/upload`). File is validated for MIME type (`application/pdf`), size ($\le 50$ MB), and path sanitization.
2. **Text & Layout Extraction**: `extract_pdf_document` extracts raw text, page numbers, tables, and bounding metadata using PyMuPDF.
3. **Semantic Chunking**: `SemanticChunker` breaks text into overlapping context chunks preserving sentence boundaries and page attribution.
4. **Entity & Fact Extraction**: `DocLinkService` extracts subject-predicate-object triples, domain entities, and metric numbers.
5. **Neo4j Graph Indexing**: `GraphService` executes parameterized Cypher queries to create `:Document`, `:Chunk`, `:Entity`, and `:Fact` nodes with `:CONTAINS` and `:RELATES_TO` edges.
6. **BGE Vector Embedding**: `SentenceTransformerEmbeddingModel` generates 384-dimensional dense vectors normalized with L2 norm on PyTorch CUDA.
7. **FAISS Vector Indexing**: `FAISSVectorStore` indexes vectors using inner product similarity (`IndexFlatIP`) and persists index files (`faiss.index`).
8. **User Query Vector Embedding**: User question is embedded into 384-dim query vector.
9. **FAISS Vector Retrieval**: FAISS searches top-10 semantic chunks by vector cosine similarity.
10. **Neo4j Graph Retrieval**: Graph retriever fetches connected subgraphs and 1-hop neighbor entities via Cypher.
11. **RRF Fusion**: `ReciprocalRankFusion` merges vector and graph candidates into a single deduplicated ranking using $S_{\text{RRF}}(c) = \frac{1}{60 + R_v} + \frac{1}{60 + R_g}$.
12. **QUBO Optimization**: `QUBOFormulator` constructs a binary optimization matrix $Q$ balancing relevance, structural graph support, diversity, and candidate limit $K=3$. Solver computes minimum energy configuration $x^* = \arg\min x^T Q x$.
13. **Grounded Context Builder**: Selected evidence chunks are formatted into structured evidence text tagged with explicit identifiers `[E1]`, `[E2]`.
14. **QLoRA Student Inference**: `StudentInferenceService` feeds strict anti-hallucination prompt to `Qwen2.5-0.5B-Instruct` + PEFT adapter.
15. **Grounding Validation**: `validate_grounded_answer` verifies cited evidence IDs, checks for invalid references, and asserts 100% numerical fact preservation.
16. **Citation UI Rendering**: React frontend receives `GroundedAnswerResponse` and displays answer text, Grounded: PASS badge, citations, and source evidence cards.
