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