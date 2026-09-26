# Demo Startup Guide & Step-by-Step Instructions

## Executive Summary
This guide provides reproducible steps to start and present the **DocLink Grounded RAG Platform** for a live demonstration.

---

## 1. Prerequisites Check
Ensure the following are installed:
- Python 3.10+
- Node.js 18+ and `npm`
- NVIDIA GPU driver (CUDA active)

---

## 2. Step-by-Step Startup Sequence

### Step 1: Start Neo4j Database (Optional / Production)
Start your local Neo4j desktop instance or Docker container:
```bash
docker run -d --name neo4j -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/doclink123 neo4j:latest
```
*(If Neo4j is offline, the backend will log a warning and fallback gracefully to FAISS vector retrieval).*

---

### Step 2: Configure Environment `.env`
Ensure `.env` exists in root:
```bash
cp .env.example .env
```

---

### Step 3: Launch FastAPI Backend Server
Open a terminal in project root:
```bash
cd Backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Verify backend health by opening `http://localhost:8000/health` in your browser.

---

### Step 4: Launch React Frontend Application
Open a second terminal in project root:
```bash
cd Frontend
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 3. Live Demo Execution Steps

1. **Upload Document**: Click **Upload Document** in the React UI and select `test sample/testreport.pdf`.
2. **Indexing Verification**: Observe status bar completing extraction and indexing.
3. **Open RAG Modal**: Click **Ask Knowledge Base (RAG)**.
4. **Execute Query**: Type domain question:
   ```text
   What sensors were used in the IoT architecture?
   ```
5. **Verify Output**:
   - Observe **Grounded: PASS** badge.
   - Inspect Grounded Answer text citing `[E1], [E2]`.
   - Point to QUBO Solver Energy (`-0.4852`) and $<5\text{ms}$ optimization latency.
   - Click evidence card to verify source text on Page 4 and Page 9.
