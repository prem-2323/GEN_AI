# 5-Minute Live SIH Demo Script — DocLink Platform

## Demo Overview
- **Title**: DocLink — Enterprise Document Intelligence & Grounded RAG Platform
- **Duration**: Exactly 5:00 minutes
- **Presenter Setup**: Screen sharing React UI at `http://localhost:5173` with backend server running at `http://localhost:8000`.

---

## Timed Presentation Script

| Timestamp | Phase / Step | Action & Dialogue | Visual / UI Focus |
|---|---|---|---|
| **0:00 – 0:30** | **Problem Statement** | *"Welcome judges. Enterprise documents like technical research reports and PDF manuals contain critical numerical data and entity relationships. Standard LLMs hallucinate numbers and lack verifiable citations. Today we present DocLink."* | Open DocLink Landing Page. |
| **0:30 – 1:00** | **Document Upload** | *"We begin by uploading our primary research paper: `testreport.pdf` — a 10-page paper on IoT sensors and machine learning."* Click **Upload Document**. | PDF drag & drop upload complete notification. |
| **1:00 – 1:45** | **Document Ingestion & Graph Indexing** | *"DocLink automatically extracts text with PyMuPDF, maps entity triples into Neo4j Knowledge Graph, generates 384-dim BGE embeddings, and indexes chunks into persistent FAISS."* | Document Processing status bar: Extracting ➔ Graph ➔ FAISS. |
| **1:45 – 2:30** | **Ask First Query** | *"Let's ask a complex domain question: 'What sensors were used in the IoT architecture?'"* Click **Ask RAG**. | RAG Search Modal opens, spinning loading indicator active. |
| **2:30 – 3:15** | **Show Evidence & Citations** | *"Within seconds, the system returns a grounded answer citing explicit evidence `[E1], [E2]`. Notice the Grounded: PASS badge."* | Point to **Grounded: PASS** badge and Source Evidence cards showing Page 4 & Page 9. |
| **3:15 – 4:00** | **Show QUBO Evidence Selection** | *"Here is our core innovation: Before feeding evidence to the LLM, DocLink formulates candidate selection as a Quadratic Unconstrained Binary Optimization (QUBO) matrix problem $x^T Q x$, selecting optimal diversity in under 5ms."* | Highlight QUBO Solver metrics: Exact Solver, Energy: `-0.4852`, Latency: `4.58ms`. |
| **4:00 – 4:30** | **Show Grounded Answer & Numerical Fact Check** | *"Let's ask about numerical performance: 'What CatBoost performance values were reported?' The system highlights exact 98.90% accuracy with 100% numerical verification."* | Display numerical answer matching source text. |
| **4:30 – 5:00** | **Architecture & Hardware Efficiency** | *"DocLink runs entirely on-premise on standard 4GB RTX 3050 GPUs using a fine-tuned QLoRA student model, consuming only 1.12 GB VRAM. Zero cloud API dependence, 100% grounded accuracy. Thank you!"* | Display Architecture Summary & System Implementation Matrix. |
