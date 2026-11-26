from pathlib import Path
import hashlib

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    Depends,
    Query,
)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import PAPERS_DIR, MAX_UPLOAD_BYTES
from app.db import get_db, create_db_and_tables

from app.schemas import AskRequest, RelationshipAnalysisRequest
from app.future_schemas.future_reviewer import FutureReviewRequest

from app.services.retrieval.indexer import PaperIndexer
from app.services.rag.rag_service import RAGService
from app.services.retrieval.vector_store import VectorStore
from app.services.claims.claim_service import ClaimService
from app.services.insights.insight_service import InsightService
from app.services.future_reviewer.service import FutureReviewerService
from app.future_schemas.research_debate import ResearchDebateRequest
from app.services.research_debate.service import ResearchDebateService
from app.reality_schemas.reality_simulator import RealitySimulationRequest
from app.services.reality_simulator.service import RealitySimulatorService
from app.workflow_schemas.agentic_workflow import AgenticWorkflowRequest
from app.services.agentic_workflow.service import AgenticWorkflowService
from app.phase7_schemas.research_workspace import WorkspaceCreate, WorkspaceUpdate, ReportGenerateRequest
from app.services.research_workspace.service import ResearchWorkspaceService
from fastapi.responses import StreamingResponse
from io import BytesIO
import json

app = FastAPI(
    title="ResearchX API",
    description=(
        "Evidence-grounded research intelligence "
        "and verifiable claim graph"
    ),
    version="1.4.0",
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


@app.on_event("startup")
def startup():
    create_db_and_tables()


@app.get("/")
def root():
    return {
        "message": "ResearchX API is running",
        "version": "1.4.0",
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

# --------------------------------------------------
# PAPER UPLOAD
# --------------------------------------------------

@app.post("/papers/upload")
async def upload_paper(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file provided.",
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    contents = await file.read()

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="The uploaded PDF is empty.",
        )

    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=(
                f"PDF exceeds the "
                f"{MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit."
            ),
        )

    if not contents.startswith(b"%PDF"):
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a valid PDF.",
        )

    sha256 = hashlib.sha256(contents).hexdigest()
    paper_id = sha256[:24]
    safe_name = Path(file.filename).name

    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    file_path = PAPERS_DIR / f"{paper_id}.pdf"

    try:
        file_path.write_bytes(contents)

        indexer = PaperIndexer()
        result = indexer.index_pdf(str(file_path), paper_id)

        service = ClaimService(db)
        service.register_paper(
            paper_id=paper_id,
            filename=safe_name,
            sha256=sha256,
            pages=result["pages"],
            chunks=result["chunks"],
        )

        return {
            "message": "Paper uploaded and indexed successfully.",
            "filename": safe_name,
            "sha256": sha256,
            **result,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Paper indexing failed: {exc}",
        ) from exc

# --------------------------------------------------
# ASK RESEARCHX
# --------------------------------------------------

@app.post("/ask")
def ask_question(request: AskRequest):
    try:
        return RAGService().answer(
            question=request.question,
            top_k=request.top_k,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

# --------------------------------------------------
# GET PAPERS
# --------------------------------------------------

@app.get("/papers")
def get_papers(db: Session = Depends(get_db)):
    from app.models import Paper

    vector_papers = VectorStore().get_papers()

    registered = {
        paper.id: paper
        for paper in db.query(Paper).all()
    }

    output = []

    for item in vector_papers:
        paper = registered.get(item["paper_id"])

        output.append({
            **item,
            "filename": (
                paper.filename if paper else item["paper_id"]
            ),
            "claims_count": (
                len(paper.claims) if paper else 0
            ),
        })

    return {"papers": output}

# --------------------------------------------------
# CLAIM EXTRACTION
# --------------------------------------------------

@app.post("/papers/{paper_id}/claims/extract")
def extract_paper_claims(
    paper_id: str,
    max_chunks: int | None = Query(
        default=None,
        ge=1,
        le=200,
    ),
    db: Session = Depends(get_db),
):
    try:
        return ClaimService(db).extract_claims(
            paper_id,
            max_chunks=max_chunks,
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Claim extraction failed: {exc}",
        ) from exc

@app.get("/claims")
def get_claims(
    paper_id: str | None = None,
    db: Session = Depends(get_db),
):
    return {
        "claims": ClaimService(db).list_claims(
            paper_id=paper_id
        )
    }

# --------------------------------------------------
# CLAIM RELATIONSHIPS
# --------------------------------------------------

@app.post("/claims/relationships/analyze")
def analyze_claim_relationships(
    request: RelationshipAnalysisRequest,
    db: Session = Depends(get_db),
):
    try:
        return ClaimService(db).analyze_relationships(
            threshold=request.similarity_threshold,
            max_pairs=request.max_pairs,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Relationship analysis failed: {exc}",
        ) from exc


@app.get("/claims/graph")
def get_claim_graph(
    paper_id: str | None = None,
    db: Session = Depends(get_db),
):
    return ClaimService(db).get_graph(
        paper_id=paper_id
    )

# --------------------------------------------------
# PHASE 2: RESEARCH INTELLIGENCE
# --------------------------------------------------

@app.post("/insights/blind-spots/analyze")
def analyze_blind_spots(
    db: Session = Depends(get_db),
):
    try:
        return InsightService(db).detect_blind_spots()

    except LookupError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Blind-spot analysis failed: {exc}",
        ) from exc


@app.post("/insights/serendipity/analyze")
def analyze_serendipity(
    db: Session = Depends(get_db),
):
    try:
        return InsightService(db).discover_serendipity()

    except LookupError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Serendipity analysis failed: {exc}",
        ) from exc

@app.get("/insights")
def get_insights(
    insight_type: str | None = None,
    db: Session = Depends(get_db),
):
    if insight_type and insight_type not in {
        "blind_spot",
        "serendipity",
    }:
        raise HTTPException(
            status_code=400,
            detail="insight_type must be blind_spot or serendipity",
        )

    return {
        "insights": InsightService(db).list_insights(
            insight_type=insight_type
        )
    }

# --------------------------------------------------
# PHASE 3: FUTURE REVIEWER
# --------------------------------------------------

@app.post("/future-reviewer/review")
def create_future_review(
    request: FutureReviewRequest,
    db: Session = Depends(get_db),
):
    try:
        return FutureReviewerService(db).review_proposal(
            request
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Future Reviewer analysis failed: {exc}",
        ) from exc

@app.get("/future-reviewer/reviews")
def get_future_reviews(
    db: Session = Depends(get_db),
):
    try:
        return FutureReviewerService(db).list_reviews()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve reviews: {exc}",
        ) from exc

@app.get("/future-reviewer/reviews/{review_id}")
def get_future_review(
    review_id: str,
    db: Session = Depends(get_db),
):
    review = FutureReviewerService(db).get_review(review_id)

    if review is None:
        raise HTTPException(
            status_code=404,
            detail="Future Reviewer report not found.",
        )

    return review

# --------------------------------------------------
# PHASE 4: RESEARCH DEBATE
# --------------------------------------------------

@app.post("/research-debate/run")
def run_research_debate(
    request: ResearchDebateRequest,
    db: Session = Depends(get_db),
):
    try:
        return ResearchDebateService(db).run_debate(
            request.future_review_id
        )

    except ValueError as exc:
        if str(exc) == "Future Reviewer report not found.":
            raise HTTPException(
                status_code=404,
                detail=str(exc),
            ) from exc

        raise HTTPException(
            status_code=502,
            detail=f"Research Debate processing error: {exc}",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Research Debate failed: {exc}",
        ) from exc

@app.get("/research-debate")
def get_research_debates(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        return {
            "debates": ResearchDebateService(db).get_debates(
                limit=limit
            )
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve debates: {exc}",
        ) from exc

@app.get("/research-debate/by-review/{future_review_id}")
def get_debates_by_review(
    future_review_id: str,
    db: Session = Depends(get_db),
):
    try:
        return {
            "debates": (
                ResearchDebateService(db).get_debates_by_review(
                    future_review_id
                )
            )
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve debates: {exc}",
        ) from exc


@app.get("/research-debate/{debate_id}")
def get_research_debate(
    debate_id: str,
    db: Session = Depends(get_db),
):
    debate = ResearchDebateService(db).get_debate(debate_id)

    if debate is None:
        raise HTTPException(
            status_code=404,
            detail="Research Debate not found.",
        )

    return debate
# --------------------------------------------------
# PHASE 5: RESEARCH REALITY SIMULATOR
# --------------------------------------------------

@app.post("/reality-simulator/run")
def run_reality_simulation(
    request: RealitySimulationRequest,
    db: Session = Depends(get_db),
):
    try:
        return RealitySimulatorService(db).run_simulation(
            request.future_review_id
        )

    except ValueError as exc:
        if str(exc) == "Future Reviewer report not found.":
            raise HTTPException(
                status_code=404,
                detail=str(exc),
            ) from exc

        raise HTTPException(
            status_code=502,
            detail=f"Reality Simulator processing error: {exc}",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Reality Simulator failed: {exc}",
        ) from exc


@app.get("/reality-simulator")
def get_reality_assessments(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        return {
            "assessments": RealitySimulatorService(db).get_assessments(
                limit=limit
            )
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve reality assessments: {exc}",
        ) from exc


@app.get("/reality-simulator/by-review/{future_review_id}")
def get_reality_assessments_by_review(
    future_review_id: str,
    db: Session = Depends(get_db),
):
    try:
        return {
            "assessments": (
                RealitySimulatorService(db).get_assessments_by_review(
                    future_review_id
                )
            )
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve assessments: {exc}",
        ) from exc


@app.get("/reality-simulator/{assessment_id}")
def get_reality_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
):
    assessment = RealitySimulatorService(db).get_assessment(
        assessment_id
    )

    if assessment is None:
        raise HTTPException(
            status_code=404,
            detail="Reality assessment not found.",
        )

    return assessment

# --------------------------------------------------
# PHASE 6: AGENTIC RESEARCH WORKFLOW
# --------------------------------------------------

@app.post("/agentic-workflows/run")
def run_agentic_workflow(
    request: AgenticWorkflowRequest,
    db: Session = Depends(get_db),
):
    try:
        return AgenticWorkflowService(db).run(
            request.request, request.future_review_id
        )
    except ValueError as exc:
        if str(exc) == "Future Reviewer report not found.":
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"Agentic workflow failed: {exc}"
        ) from exc

@app.get("/agentic-workflows")
def get_agentic_workflows(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return {"workflows": AgenticWorkflowService(db).list_runs(limit)}

@app.get("/agentic-workflows/{workflow_id}")
def get_agentic_workflow(
    workflow_id: str, db: Session = Depends(get_db),
):
    workflow = AgenticWorkflowService(db).get_run(workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Agentic workflow not found.")
    return workflow


# --------------------------------------------------
# PHASE 7: RESEARCH WORKSPACE & REPORT GENERATION
# --------------------------------------------------
@app.get("/research-workspaces")
def list_research_workspaces(db: Session = Depends(get_db)):
    return {"workspaces": ResearchWorkspaceService(db).list_workspaces()}

@app.post("/research-workspaces")
def create_research_workspace(request: WorkspaceCreate, db: Session = Depends(get_db)):
    try: return ResearchWorkspaceService(db).create_workspace(request)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/research-workspaces/{workspace_id}")
def get_research_workspace(workspace_id: str, db: Session = Depends(get_db)):
    item=ResearchWorkspaceService(db).get_workspace(workspace_id)
    if not item: raise HTTPException(status_code=404, detail="Research workspace not found.")
    return item

@app.patch("/research-workspaces/{workspace_id}")
def update_research_workspace(workspace_id: str, request: WorkspaceUpdate, db: Session = Depends(get_db)):
    try: item=ResearchWorkspaceService(db).update_workspace(workspace_id,request)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
    if not item: raise HTTPException(status_code=404,detail="Research workspace not found.")
    return item

@app.delete("/research-workspaces/{workspace_id}")
def delete_research_workspace(workspace_id: str, db: Session = Depends(get_db)):
    if not ResearchWorkspaceService(db).delete_workspace(workspace_id): raise HTTPException(status_code=404,detail="Research workspace not found.")
    return {"message":"Workspace and its saved reports deleted."}

@app.post("/research-workspaces/{workspace_id}/reports/generate")
def generate_research_report(workspace_id: str, request: ReportGenerateRequest, db: Session = Depends(get_db)):
    report=ResearchWorkspaceService(db).generate_report(workspace_id,request)
    if not report: raise HTTPException(status_code=404,detail="Research workspace not found.")
    return report

@app.get("/research-workspaces/{workspace_id}/reports")
def list_research_reports(workspace_id: str, db: Session = Depends(get_db)):
    if not ResearchWorkspaceService(db).get_workspace(workspace_id): raise HTTPException(status_code=404,detail="Research workspace not found.")
    return {"reports":ResearchWorkspaceService(db).list_reports(workspace_id)}

@app.get("/research-reports/{report_id}")
def get_research_report(report_id: str, db: Session = Depends(get_db)):
    report=ResearchWorkspaceService(db).get_report(report_id)
    if not report: raise HTTPException(status_code=404,detail="Research report not found.")
    return report

def _report_plain_text(report):
    lines=[report["title"],"Generated: "+str(report.get("created_at","")),""]
    for sec in report.get("sections",[]):
        lines.extend([sec.get("heading","Section"),"="*max(4,len(sec.get("heading","Section"))),""])
        if sec.get("content"): lines.extend([str(sec["content"]),""])
        for item in sec.get("items",[]): lines.extend([json.dumps(item,ensure_ascii=False,indent=2,default=str),""])
    lines.extend(["Source manifest",json.dumps(report.get("source_manifest",[]),ensure_ascii=False,indent=2,default=str)])
    return "\n".join(lines)

@app.get("/research-reports/{report_id}/export/txt")
def export_research_report_txt(report_id: str, db: Session = Depends(get_db)):
    report=ResearchWorkspaceService(db).get_report(report_id)
    if not report: raise HTTPException(status_code=404,detail="Research report not found.")
    data=_report_plain_text(report).encode("utf-8")
    return StreamingResponse(BytesIO(data),media_type="text/plain; charset=utf-8",headers={"Content-Disposition":f'attachment; filename="researchx-report-{report_id[:8]}.txt"'})

@app.get("/research-reports/{report_id}/export/pdf")
def export_research_report_pdf(report_id: str, db: Session = Depends(get_db)):
    report=ResearchWorkspaceService(db).get_report(report_id)
    if not report: raise HTTPException(status_code=404,detail="Research report not found.")
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        buf=BytesIO(); doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=18*mm,bottomMargin=18*mm)
        styles=getSampleStyleSheet(); story=[Paragraph(report["title"].replace("&","&amp;"),styles["Title"]),Spacer(1,10)]
        for sec in report.get("sections",[]):
            heading=sec.get("heading","Section").replace("&","&amp;")
            story.append(Paragraph(heading,styles["Heading2"]))
            if sec.get("content"):
                for para in str(sec["content"]).split("\n"):
                    if para.strip(): story.append(Paragraph(para.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"),styles["BodyText"]))
                    story.append(Spacer(1,4))
            for item in sec.get("items",[]): story.append(Preformatted(json.dumps(item,ensure_ascii=False,indent=2,default=str),ParagraphStyle("small",parent=styles["Code"],fontSize=7,leading=9)))
            story.append(Spacer(1,8))
        doc.build(story); buf.seek(0)
        return StreamingResponse(buf,media_type="application/pdf",headers={"Content-Disposition":f'attachment; filename="researchx-report-{report_id[:8]}.pdf"'})
    except ImportError as exc: raise HTTPException(status_code=501,detail="PDF export dependency missing. Install reportlab.") from exc

@app.get("/research-reports/{report_id}/export/docx")
def export_research_report_docx(report_id: str, db: Session = Depends(get_db)):
    report=ResearchWorkspaceService(db).get_report(report_id)
    if not report: raise HTTPException(status_code=404,detail="Research report not found.")
    try:
        from docx import Document
        buf=BytesIO(); doc=Document(); doc.add_heading(report["title"],0)
        for sec in report.get("sections",[]):
            doc.add_heading(sec.get("heading","Section"),level=1)
            if sec.get("content"): doc.add_paragraph(str(sec["content"]))
            for item in sec.get("items",[]): doc.add_paragraph(json.dumps(item,ensure_ascii=False,indent=2,default=str))
        doc.add_heading("Source manifest",level=1); doc.add_paragraph(json.dumps(report.get("source_manifest",[]),ensure_ascii=False,indent=2,default=str))
        doc.save(buf); buf.seek(0)
        return StreamingResponse(buf,media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",headers={"Content-Disposition":f'attachment; filename="researchx-report-{report_id[:8]}.docx"'})
    except ImportError as exc: raise HTTPException(status_code=501,detail="DOCX export dependency missing. Install python-docx.") from exc