# ResearchX

ResearchX is an AI-powered research paper analysis system designed to help users understand and explore research papers through semantic search and evidence-grounded question answering.

The system allows users to upload research papers, process their content, store semantic representations, retrieve relevant evidence, and ask questions about the indexed research papers.

---

## Project Status

### Current Milestone: 50% Implementation

The current implementation focuses on the core research-paper processing and Retrieval-Augmented Generation (RAG) pipeline.

### Implemented

- PDF upload
- PDF text extraction
- Text cleaning
- Text chunking
- Semantic embeddings
- Vector database storage
- Semantic retrieval
- Retrieval-Augmented Generation (RAG)
- Groq LLM integration
- Evidence-grounded responses
- Source and page information
- Multi-paper knowledge base
- Duplicate paper detection
- React-based frontend
- FastAPI backend

### Planned

The remaining implementation will extend ResearchX with:

- Research insight extraction
- Cross-paper comparison
- Method and finding analysis
- Limitation identification
- Research-gap analysis
- Agentic AI capabilities
- MCP-based tool interaction
- Advanced research workflows

---

## System Architecture

```text
                    ResearchX
                       |
              +--------+--------+
              |                 |
         PDF Upload       Research Query
              |                 |
              v                 v
       PDF Text Extraction   Query Processing
              |                 |
              v                 v
         Text Cleaning       Retrieval
              |                 |
              v                 v
           Chunking          Evidence
              |                 |
              v                 |
         Embeddings             |
              |                 |
              v                 |
          ChromaDB <------------+
              |
              v
       Relevant Evidence
              |
              v
          Groq LLM
              |
              v
     Evidence-Grounded Answer
              |
              v
       Source Information
```

---

## Technology Stack

### Backend

- Python
- FastAPI
- PyMuPDF
- Sentence Transformers
- ChromaDB
- Groq API
- Pytest

### Frontend

- React
- Vite
- JavaScript
- CSS
- Lucide React

### AI / NLP

- Sentence embeddings for semantic representation
- Vector similarity search
- Retrieval-Augmented Generation
- Large Language Model based response generation

---

## Project Structure

```text
ResearchX/
│
├── backend/
│   │
│   ├── app/
│   │   ├── services/
│   │   │   ├── ingestion/
│   │   │   │   ├── pdf_loader.py
│   │   │   │   ├── text_cleaner.py
│   │   │   │   └── chunker.py
│   │   │   │
│   │   │   ├── embeddings/
│   │   │   │   └── embedding_service.py
│   │   │   │
│   │   │   ├── retrieval/
│   │   │   │   ├── vector_store.py
│   │   │   │   └── retriever.py
│   │   │   │
│   │   │   ├── rag/
│   │   │   │   └── rag_service.py
│   │   │   │
│   │   │   └── indexing/
│   │   │       └── indexer.py
│   │   │
│   │   ├── config.py
│   │   └── main.py
│   │
│   ├── tests/
│   │   ├── test_ingestion.py
│   │   ├── test_retrieval.py
│   │   ├── test_rag.py
│   │   └── test_upload.py
│   │
│   └── requirements.txt
│
├── frontend/
│   │
│   ├── src/
│   │   ├── App.jsx
│   │   └── App.css
│   │
│   ├── package.json
│   └── vite.config.js
│
├── data/
│   ├── papers/
│   ├── processed/
│   └── vector_store/
│
├── .env.example
├── .gitignore
└── README.md
```

---

## Core Workflow

### 1. Paper Upload

The user uploads a research paper in PDF format.

```text
PDF
 ↓
FastAPI Upload API
```

---

### 2. PDF Ingestion

The uploaded PDF is processed page by page and its textual content is extracted.

```text
PDF
 ↓
Page-wise Text
```

---

### 3. Text Processing

Extracted text is cleaned and divided into smaller chunks suitable for semantic retrieval.

```text
Raw Text
 ↓
Cleaned Text
 ↓
Text Chunks
```

---

### 4. Embedding Generation

Each text chunk is converted into a numerical vector representation using a sentence embedding model.

```text
Text Chunk
 ↓
Embedding Model
 ↓
Vector
```

---

### 5. Vector Storage

The embeddings and their associated metadata are stored in ChromaDB.

Metadata includes information such as:

- Paper ID
- Chunk ID
- Page number

---

### 6. Semantic Retrieval

When a user asks a question, the question is converted into an embedding.

The system searches the vector database for the most semantically relevant chunks.

```text
User Question
 ↓
Query Embedding
 ↓
ChromaDB Similarity Search
 ↓
Top-k Relevant Chunks
```

---

### 7. Retrieval-Augmented Generation

The retrieved evidence is supplied to the LLM.

The model is instructed to answer using the supplied evidence rather than relying on unsupported information.

```text
Relevant Evidence
       +
User Question
       ↓
     Groq LLM
       ↓
Grounded Answer
```

The response also includes the paper and page information associated with the retrieved evidence.

---

## API

The backend is implemented using FastAPI.

When the backend is running, the interactive API documentation is available through:

```text
http://127.0.0.1:8000/docs
```

### Main functionality

```text
POST /papers/upload
```

Uploads and indexes a research paper.

```text
GET /papers
```

Returns the papers currently available in the knowledge base.

```text
POST /ask
```

Accepts a research question and returns an evidence-grounded answer.

---

## Running the Backend

Navigate to the backend directory:

```bash
cd backend
```

Create and activate a virtual environment:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```env
LLM_API_KEY=your_groq_api_key
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=your_groq_model
```

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

---

## Running the Frontend

Navigate to the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Open the URL shown by Vite, usually:

```text
http://localhost:5173
```

---

## Testing

From the backend directory:

```bash
python -m pytest tests/test_ingestion.py -s
```

```bash
python -m pytest tests/test_retrieval.py -s
```

```bash
python -m pytest tests/test_rag.py -s
```

```bash
python -m pytest tests/test_upload.py -s
```

The tests cover the major components of the current implementation.

---

## Current Demonstration

The current prototype demonstrates the following complete flow:

```text
Upload Research Paper
        ↓
Extract PDF Text
        ↓
Clean Text
        ↓
Create Chunks
        ↓
Generate Embeddings
        ↓
Store in ChromaDB
        ↓
Ask Research Question
        ↓
Retrieve Relevant Evidence
        ↓
Generate RAG Response
        ↓
Display Answer + Sources
```

The system also supports storing multiple research papers in a shared knowledge base.

---

## Future Scope

ResearchX will be extended beyond basic RAG to provide higher-level research assistance.

Planned capabilities include:

1. Automatic extraction of research methods, findings and limitations.
2. Cross-paper comparison.
3. Identification of similarities and differences between approaches.
4. Research-gap identification.
5. Agentic research workflows.
6. Tool-based interaction using MCP.
7. More advanced evidence tracing and research exploration.

These additions will transform ResearchX from a simple question-answering system into a research-analysis assistant.

---

## Authors

ResearchX is an academic project developed as part of the Text Analytics course.
---

## Phase 6 — Agentic Research Workflow

Phase 6 adds a central workflow orchestrator that interprets a research task, selects a bounded sequence of existing ResearchX capabilities, executes them, and stores the execution history.

### Capabilities

- LLM-assisted planning using the configured Groq model.
- Allowlisted tool execution; the planner cannot call arbitrary functions or endpoints.
- Reuses Ask ResearchX retrieval, Claim Graph inspection, claim relationship analysis, Research Blind Spot Detector, Research Serendipity Engine, Research Debate, and Reality Simulator.
- Debate and Reality Simulator steps require a valid saved `future_review_id`.
- Stores the plan, per-tool status/output, workflow status, and summary in `agentic_workflow_runs`.
- Frontend Agentic Workflow tab includes task entry, optional Future Reviewer report selection, execution plan, expandable tool results, and saved workflow history.

### API endpoints

- `POST /agentic-workflows/run` — execute a workflow.
- `GET /agentic-workflows` — list recent workflows (`limit` 1–100, default 20).
- `GET /agentic-workflows/{workflow_id}` — retrieve a saved workflow.

Example request:

```json
{
  "request": "Compare the main findings across my uploaded papers, identify conflicting claims, and detect research gaps."
}
```

To enable proposal-specific Debate or Reality Simulator steps, include a saved Future Reviewer report ID:

```json
{
  "request": "Challenge this proposal and assess its implementation feasibility.",
  "future_review_id": "<saved-future-review-id>"
}
```

### Database note

The new `agentic_workflow_runs` table is registered through the existing SQLAlchemy `create_all` startup process. Restart the backend after updating the code. Existing data tables are not intentionally dropped or reset.

### Evidence and execution limitations

- Workflow results are grounded in the papers and records available in this ResearchX instance.
- A tool can fail independently; the workflow stores the failure and continues to later planned steps.
- The workflow planner is LLM-assisted, but execution is restricted to the server-side allowlist.
- This is an internal MCP-inspired tool registry/orchestrator, not a standalone MCP server or a connection to arbitrary external MCP servers.


## Phase 7 — Research Workspace & Report Generation

Phase 7 adds persistent research workspaces and report snapshots. A workspace groups a research question, description, and selected uploaded paper IDs. Reports collect claims and their stored evidence for the selected papers, and include Research Intelligence / Future Reviewer / Agentic Workflow material only when those records cite claims from the selected papers. The report clearly labels AI-generated analysis separately from paper-derived evidence.

### Phase 7 setup

Install the updated backend dependencies after activating the backend virtual environment:

```bash
pip install -r requirements.txt
```

Restart the backend and frontend. The database creates the two new tables automatically on startup: `research_workspaces` and `research_reports`. Existing data is preserved.

### Phase 7 API

- `GET /research-workspaces` — list workspaces
- `POST /research-workspaces` — create a workspace
- `GET /research-workspaces/{workspace_id}` — open a workspace
- `PATCH /research-workspaces/{workspace_id}` — update a workspace
- `DELETE /research-workspaces/{workspace_id}` — delete workspace and its saved reports
- `POST /research-workspaces/{workspace_id}/reports/generate` — generate and save a report
- `GET /research-workspaces/{workspace_id}/reports` — list saved reports
- `GET /research-reports/{report_id}` — retrieve a report
- `GET /research-reports/{report_id}/export/pdf` — export PDF
- `GET /research-reports/{report_id}/export/docx` — export DOCX
- `GET /research-reports/{report_id}/export/txt` — export text

Reports are snapshots: generate a new report after updating workspace papers or after creating new analyses. PDF and DOCX export use `reportlab` and `python-docx`, added to `requirements.txt`.

### Important evidence note

The report is a research-organizing aid, not a validated systematic review. It preserves claim IDs, evidence quotations, page numbers and paper IDs available in the database. AI-generated insights and proposal reviews are marked as AI-generated. Verify all claims and references against the original PDFs before using the report in academic or publication work.

---

## Phase 8 – Model Context Protocol (MCP) Integration

ResearchX includes a separate MCP server that exposes existing ResearchX capabilities to MCP-compatible clients. It reuses the FastAPI backend and its existing services; it does not create a second database or duplicate research logic.

### MCP capabilities

**Tools:** paper search, RAG question answering, claim retrieval, claim graph retrieval, blind-spot analysis, serendipity discovery, saved insight listing, Future Reviewer, Research Debate, Reality Simulator, Phase 6 agentic workflow, workspace listing/creation, and report generation.

**Resources:** `researchx://papers`, `researchx://claims`, `researchx://claim-graph`, `researchx://insights`, `researchx://workspaces`, and `researchx://reports/{report_id}`.

**Prompts:** `literature_review`, `research_gap_analysis`, and `proposal_evaluation`.

### Install

Use the same Python virtual environment as the backend:

```powershell
cd backend
.\venv\Scripts\activate
pip install -r requirements.txt
```

The project pins the official MCP Python SDK to its v1.x compatibility line (`mcp>=1.28,<2`) so the server implementation and client smoke test use a consistent API. Do not remove the upper bound without migrating the imports and server API to SDK v2.

### Configure

Copy `.env.mcp.example` to `.env` (or merge these variables into your existing backend `.env`). Generate a long random token and set `MCP_API_TOKEN`. Keep the token private and do not commit `.env`.

Example PowerShell token generation:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Set the generated value as `MCP_API_TOKEN` in `.env`. The MCP server refuses to start if the token is missing. The HTTP MCP endpoint requires `Authorization: Bearer <MCP_API_TOKEN>`.

### Run

Terminal 1 – existing ResearchX API:

```powershell
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --port 8001
```

Terminal 2 – MCP server:

```powershell
cd backend
.\venv\Scripts\activate
python -m app.mcp_server.server
```

MCP Streamable HTTP endpoint: `http://127.0.0.1:8002/mcp`.

### Test with MCP Inspector

Install/use Node.js and run:

```powershell
npx -y @modelcontextprotocol/inspector
```

In Inspector, select Streamable HTTP and enter `http://127.0.0.1:8002/mcp`. Add request header:

```json
{"Authorization":"Bearer YOUR_MCP_API_TOKEN"}
```

Then inspect **Tools**, **Resources**, and **Prompts**. Start with `search_research_papers`, `ask_research_corpus`, and `get_paper_claims`. For write tools, `create_research_workspace` and `generate_research_report` require `confirm=true`.

### Test using the bundled MCP client

With both servers running and `MCP_API_TOKEN` configured:

```powershell
python -m app.mcp_server.client_check
```

### Connect an MCP-compatible desktop client

Configure a client that supports remote Streamable HTTP MCP servers with:

- URL: `http://127.0.0.1:8002/mcp`
- Header: `Authorization: Bearer YOUR_MCP_API_TOKEN`

For remote access, do not expose the development server directly to the public internet. Put it behind HTTPS, use a strong unique token, restrict network access, and rotate credentials if exposed. `127.0.0.1` intentionally makes the development server local-only by default.

### Architecture and safeguards

- The MCP server is a separate process and port (8002); the existing React UI and FastAPI API (8001) remain available independently.
- MCP tools call the existing REST API, which in turn uses existing ResearchX services and database records.
- Reads are available directly. Workspace creation and report generation require an explicit `confirm=true` argument. There is intentionally no MCP workspace-delete tool.
- Review IDs and paper IDs must be real IDs returned by ResearchX; the MCP layer does not invent them.
- Research outputs remain subject to the same corpus limitations as the underlying ResearchX features.
