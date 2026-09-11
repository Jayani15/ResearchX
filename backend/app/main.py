from pathlib import Path

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel

from app.config import PAPERS_DIR
from app.services.retrieval.indexer import PaperIndexer
from app.services.rag.rag_service import RAGService
from app.services.retrieval.vector_store import VectorStore


app = FastAPI(
    title="ResearchX API",
    description="Research Paper Intelligence System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AskRequest(BaseModel):
    question: str
    top_k: int = 5


@app.get("/")
def root(): 
    return {
        "message": "ResearchX API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/papers/upload")
async def upload_paper(
    file: UploadFile = File(...)
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file provided."
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    PAPERS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    file_path = PAPERS_DIR / file.filename

    try:

        contents = await file.read()

        with open(file_path, "wb") as f:
            f.write(contents)

        paper_id = Path(
            file.filename
        ).stem

        indexer = PaperIndexer()

        result = indexer.index_pdf(
            file_path=str(file_path),
            paper_id=paper_id,
        )

        return {
            "message":
                "Paper uploaded and indexed successfully.",
            "filename":
                file.filename,
            **result,
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.post("/ask")
def ask_question(request: AskRequest):

    rag = RAGService()

    result = rag.answer(
        question=request.question,
        top_k=request.top_k,
    )

    return result

@app.get("/papers")
def get_papers():

    vector_store = VectorStore()

    return {
        "papers": vector_store.get_papers()
    }