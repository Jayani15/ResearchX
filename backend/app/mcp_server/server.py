"""ResearchX MCP server (official MCP Python SDK v1 compatibility line).

The MCP server is a separate process. It calls the existing FastAPI application,
so business logic and persistence remain owned by ResearchX's existing services.
"""
from __future__ import annotations

import json
import os
import hmac
import contextlib
from typing import Any

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import uvicorn

load_dotenv()

BACKEND_URL = os.getenv("RESEARCHX_API_URL", "http://127.0.0.1:8001").rstrip("/")
MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.getenv("MCP_PORT", "8002"))
MCP_API_TOKEN = os.getenv("MCP_API_TOKEN", "").strip()

if not MCP_API_TOKEN:
    raise RuntimeError("MCP_API_TOKEN must be set before starting the ResearchX MCP server.")

mcp = FastMCP(
    "ResearchX MCP Server",
    instructions=(
        "Access the user's ResearchX research corpus and saved analysis. "
        "Ground answers in returned paper evidence. Clearly distinguish source evidence "
        "from AI-generated interpretations. Do not invent paper IDs or review IDs."
    ),
    stateless_http=True,
    json_response=True,
)

def _request(method: str, path: str, *, params: dict | None = None, body: dict | None = None) -> Any:
    """Call the existing ResearchX API and return JSON with useful errors."""
    try:
        response = httpx.request(
            method,
            f"{BACKEND_URL}{path}",
            params=params,
            json=body,
            timeout=180.0,
        )
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        return {"message": "ResearchX API returned a non-JSON response.", "status_code": response.status_code}
    except httpx.HTTPStatusError as exc:
        try:
            detail = exc.response.json()
        except Exception:
            detail = exc.response.text[:1000]
        return {"error": "researchx_api_error", "status_code": exc.response.status_code, "detail": detail}
    except httpx.RequestError as exc:
        return {"error": "researchx_api_unavailable", "detail": str(exc), "backend_url": BACKEND_URL}


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


# ------------------------------- TOOLS ------------------------------------

@mcp.tool()
def search_research_papers(query: str = "") -> dict:
    """List uploaded/indexed research papers. Use query to filter filenames or IDs."""
    result = _request("GET", "/papers")
    if isinstance(result, dict) and isinstance(result.get("papers"), list) and query.strip():
        needle = query.casefold()
        result["papers"] = [p for p in result["papers"] if needle in _json_text(p).casefold()]
    return result

@mcp.tool()
def ask_research_corpus(question: str, top_k: int = 5) -> dict:
    """Answer a question using ResearchX RAG over uploaded papers, including retrieved sources."""
    if not question.strip():
        return {"error": "question_required"}
    return _request("POST", "/ask", body={"question": question, "top_k": max(1, min(top_k, 20))})

@mcp.tool()
def get_paper_claims(paper_id: str = "") -> dict:
    """Get extracted claims, optionally limited to one exact uploaded paper ID."""
    params = {"paper_id": paper_id} if paper_id else None
    return _request("GET", "/claims", params=params)

@mcp.tool()
def get_claim_graph(paper_id: str = "") -> dict:
    """Read the existing claim graph, optionally filtered by paper ID."""
    params = {"paper_id": paper_id} if paper_id else None
    return _request("GET", "/claims/graph", params=params)

@mcp.tool()
def analyze_research_gaps() -> dict:
    """Run ResearchX Blind Spot analysis on the indexed research corpus."""
    return _request("POST", "/insights/blind-spots/analyze", body={})

@mcp.tool()
def discover_cross_paper_connections() -> dict:
    """Run ResearchX Serendipity analysis to find possible cross-paper connections."""
    return _request("POST", "/insights/serendipity/analyze", body={})

@mcp.tool()
def list_research_insights(insight_type: str = "") -> dict:
    """List saved insights. insight_type may be blind_spot or serendipity."""
    params = {"insight_type": insight_type} if insight_type else None
    return _request("GET", "/insights", params=params)

@mcp.tool()
def review_research_proposal(
    research_title: str,
    research_idea: str,
    proposed_methodology: str = "",
    proposed_dataset: str = "",
    proposed_metrics: str = "",
) -> dict:
    """Run Future Reviewer on a proposal and return its saved review ID."""
    return _request("POST", "/future-reviewer/review", body={
        "research_title": research_title,
        "research_idea": research_idea,
        "proposed_methodology": proposed_methodology,
        "proposed_dataset": proposed_dataset,
        "proposed_metrics": proposed_metrics,
    })

@mcp.tool()
def run_research_debate(future_review_id: str) -> dict:
    """Run Blue Team, Red Team and Judge using an existing saved Future Reviewer ID."""
    if not future_review_id.strip():
        return {"error": "future_review_id_required"}
    return _request("POST", "/research-debate/run", body={"future_review_id": future_review_id})

@mcp.tool()
def simulate_research_feasibility(future_review_id: str) -> dict:
    """Run Reality Simulator for an existing saved Future Reviewer report."""
    if not future_review_id.strip():
        return {"error": "future_review_id_required"}
    return _request("POST", "/reality-simulator/run", body={"future_review_id": future_review_id})

@mcp.tool()
def run_agentic_research_workflow(request: str, future_review_id: str = "") -> dict:
    """Run the existing Phase 6 orchestrator; supply a real saved review ID when needed."""
    body = {"request": request}
    if future_review_id.strip():
        body["future_review_id"] = future_review_id
    return _request("POST", "/agentic-workflows/run", body=body)

@mcp.tool()
def list_research_workspaces() -> dict:
    """List saved ResearchX workspaces."""
    return _request("GET", "/research-workspaces")

@mcp.tool()
def create_research_workspace(
    title: str,
    research_question: str = "",
    description: str = "",
    paper_ids: list[str] | None = None,
    confirm: bool = False,
) -> dict:
    """Create a workspace. Set confirm=true to perform this persistent write."""
    if not confirm:
        return {"confirmation_required": True, "message": "Call again with confirm=true to create this workspace."}
    return _request("POST", "/research-workspaces", body={
        "title": title,
        "research_question": research_question,
        "description": description,
        "paper_ids": paper_ids or [],
    })

@mcp.tool()
def generate_research_report(
    workspace_id: str,
    title: str = "",
    confirm: bool = False,
) -> dict:
    """Generate and save a report for an existing workspace; requires confirm=true."""
    if not confirm:
        return {"confirmation_required": True, "message": "Call again with confirm=true to generate and save this report."}
    body: dict[str, Any] = {
        "include_claims": True,
        "include_insights": True,
        "include_reviews": True,
        "include_workflows": True,
    }
    if title.strip():
        body["title"] = title
    return _request("POST", f"/research-workspaces/{workspace_id}/reports/generate", body=body)


# ------------------------------ RESOURCES ---------------------------------

@mcp.resource("researchx://papers")
def papers_resource() -> str:
    """Catalogue of papers uploaded and indexed in ResearchX."""
    return _json_text(_request("GET", "/papers"))

@mcp.resource("researchx://claims")
def claims_resource() -> str:
    """Extracted claims and their evidence metadata."""
    return _json_text(_request("GET", "/claims"))

@mcp.resource("researchx://claim-graph")
def claim_graph_resource() -> str:
    """Current claim graph nodes and relationships."""
    return _json_text(_request("GET", "/claims/graph"))

@mcp.resource("researchx://insights")
def insights_resource() -> str:
    """Saved Blind Spot and Serendipity insights."""
    return _json_text(_request("GET", "/insights"))

@mcp.resource("researchx://workspaces")
def workspaces_resource() -> str:
    """Saved research workspaces."""
    return _json_text(_request("GET", "/research-workspaces"))

@mcp.resource("researchx://reports/{report_id}")
def report_resource(report_id: str) -> str:
    """Read one saved report by its exact report ID."""
    return _json_text(_request("GET", f"/research-reports/{report_id}"))

# -------------------------------- PROMPTS ---------------------------------

@mcp.prompt()
def literature_review(topic: str, paper_scope: str = "uploaded ResearchX papers") -> str:
    """Create an evidence-grounded literature review prompt."""
    return (
        f"Prepare a structured literature review on: {topic}. Scope: {paper_scope}. "
        "Use ResearchX paper search and RAG tools. Cite paper identifiers and retrieved evidence. "
        "Separate reported findings from interpretation, identify disagreements, and state corpus limitations. "
        "Do not invent citations or results."
    )

@mcp.prompt()
def research_gap_analysis(topic: str) -> str:
    """Create a research-gap analysis prompt grounded in the uploaded corpus."""
    return (
        f"Analyze research gaps for: {topic}. Inspect claims, claim relationships, and saved blind-spot insights. "
        "For every proposed gap, provide supporting paper evidence, explain why it matters, and label hypotheses as suggestions."
    )

@mcp.prompt()
def proposal_evaluation(research_title: str, research_idea: str) -> str:
    """Create a critical research proposal evaluation prompt."""
    return (
        f"Evaluate this proposal: {research_title}. Idea: {research_idea}. "
        "Use the Future Reviewer tool and, when the user requests it, debate and feasibility tools. "
        "Distinguish corpus-supported novelty observations from uncertain novelty judgments."
    )

class MCPBearerAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Protect every MCP endpoint. Health checks are intentionally not exposed here.
        supplied = request.headers.get("authorization", "")
        expected = f"Bearer {MCP_API_TOKEN}"
        if not hmac.compare_digest(supplied, expected):
            return JSONResponse({"error": "unauthorized", "message": "A valid MCP bearer token is required."}, status_code=401)
        return await call_next(request)

@contextlib.asynccontextmanager
async def lifespan(_app):
    async with mcp.session_manager.run():
        yield

app = Starlette(
    routes=[Mount("/", app=mcp.streamable_http_app())],
    lifespan=lifespan,
)
app.add_middleware(MCPBearerAuthMiddleware)

if __name__ == "__main__":
    uvicorn.run(app, host=MCP_HOST, port=MCP_PORT, log_level="info")