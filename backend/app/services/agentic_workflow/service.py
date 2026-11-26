import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import AgenticWorkflowRun, FutureReview
from app.services.llm.llm_service import LLMService
from app.services.research_debate.json_utils import parse_llm_json
from app.services.rag.rag_service import RAGService
from app.services.claims.claim_service import ClaimService
from app.services.insights.insight_service import InsightService
from app.services.research_debate.service import ResearchDebateService
from app.services.reality_simulator.service import RealitySimulatorService

class AgenticWorkflowService:
    """Plans and executes a bounded set of existing ResearchX capabilities."""

    TOOL_CATALOG = {
        "retrieve_research": "Answer a research question using indexed paper passages and return source passages.",
        "inspect_claim_graph": "Inspect extracted claims and their existing relationships across uploaded papers.",
        "analyze_relationships": "Find and classify relationships between extracted claims; useful for comparisons and disagreements.",
        "detect_blind_spots": "Find underexplored areas and limitations within the uploaded paper corpus.",
        "discover_serendipity": "Find defensible cross-paper connections that may inspire new research directions; requires at least two papers.",
        "run_research_debate": "Run Blue Team, Red Team, and Judge against a saved Future Reviewer report; requires future_review_id.",
        "simulate_reality": "Assess practical feasibility, resources, cost, ethics, accessibility, and risks for a saved Future Reviewer report; requires future_review_id.",
    }

    def __init__(self, db: Session):
        self.db = db

    def _plan(self, request: str, future_review_id: str | None) -> list[dict]:
        available = dict(self.TOOL_CATALOG)
        if not future_review_id:
            available.pop("run_research_debate")
            available.pop("simulate_reality")
        prompt = f"""You are the workflow planner for ResearchX. Select only tools needed to satisfy the user's request.\n\nUSER REQUEST:\n{request}\n\nAVAILABLE TOOLS (tool name: purpose):\n{available}\n\nReturn ONLY JSON in this exact shape:\n{{\"steps\":[{{\"tool\":\"exact_tool_name\",\"reason\":\"short reason\"}}]}}\n\nRules:\n- Select between 1 and 5 tools.\n- Use only exact tool names from the available list.\n- Put tools in execution order.\n- Usually include retrieve_research when the request asks a factual question about the uploaded papers.\n- Use inspect_claim_graph for claim-level overview or graph questions.\n- Use analyze_relationships for comparison, agreement, disagreement, or conflict analysis.\n- Use detect_blind_spots only when gaps/limitations are requested.\n- Use discover_serendipity only when unexpected connections/new directions are requested.\n- Debate and reality simulation are available only when a saved Future Reviewer report ID is supplied.\n- Do not select every tool by default.\n- If the request is broad, choose the smallest useful sequence.\n"""
        try:
            parsed = parse_llm_json(LLMService().generate(prompt, max_completion_tokens=700, temperature=0.0))
            raw_steps = parsed.get("steps", []) if isinstance(parsed, dict) else []
        except Exception:
            raw_steps = self._fallback_plan(request, future_review_id)

        seen = set()
        plan = []
        for item in raw_steps:
            if not isinstance(item, dict):
                continue
            tool = item.get("tool")
            if tool not in available or tool in seen:
                continue
            seen.add(tool)
            plan.append({"tool": tool, "reason": str(item.get("reason") or self.TOOL_CATALOG[tool])[:500]})
            if len(plan) == 5:
                break
        if not plan:
            plan = self._fallback_plan(request, future_review_id)
        return plan

    def _fallback_plan(self, request: str, future_review_id: str | None) -> list[dict]:
        text = request.lower()
        plan = [{"tool": "retrieve_research", "reason": "Retrieve relevant evidence from the uploaded papers."}]
        if any(word in text for word in ["claim", "graph", "evidence", "relationship"]):
            plan.append({"tool": "inspect_claim_graph", "reason": "Inspect extracted claims and their evidence links."})
        if any(word in text for word in ["conflict", "contradict", "disagree", "compare", "relationship"]):
            plan.append({"tool": "analyze_relationships", "reason": "Analyze relationships and potential disagreements between claims."})
        if any(word in text for word in ["gap", "blind spot", "limitation", "underexplored"]):
            plan.append({"tool": "detect_blind_spots", "reason": "Identify gaps and limitations in the uploaded corpus."})
        if any(word in text for word in ["serendipity", "unexpected", "cross-domain", "new direction"]):
            plan.append({"tool": "discover_serendipity", "reason": "Search for cross-paper connections."})
        if future_review_id and any(word in text for word in ["debate", "challenge", "defend"]):
            plan.append({"tool": "run_research_debate", "reason": "Challenge and evaluate the saved proposal."})
        if future_review_id and any(word in text for word in ["feasib", "reality", "cost", "implement"]):
            plan.append({"tool": "simulate_reality", "reason": "Evaluate practical feasibility of the saved proposal."})
        return plan[:5]

    def _execute_tool(self, tool: str, request: str, future_review_id: str | None):
        if tool == "retrieve_research":
            return RAGService().answer(request, top_k=5)
        if tool == "inspect_claim_graph":
            claims = ClaimService(self.db).list_claims()
            graph = ClaimService(self.db).get_graph()
            compact_graph = {
                "nodes": graph.get("nodes", [])[:80],
                "edges": graph.get("edges", [])[:120],
            }
            return {
                "claim_count": len(claims),
                "node_count": len(graph.get("nodes", [])),
                "edge_count": len(graph.get("edges", [])),
                "claims": claims[:30],
                "graph_sample": compact_graph,
            }
        if tool == "analyze_relationships":
            claims = ClaimService(self.db).list_claims()
            if len(claims) < 2:
                return {"message": "At least two extracted claims are required.", "relationships": []}
            return ClaimService(self.db).analyze_relationships(threshold=0.62, max_pairs=60)
        if tool == "detect_blind_spots":
            return InsightService(self.db).detect_blind_spots()
        if tool == "discover_serendipity":
            return InsightService(self.db).discover_serendipity()
        if tool == "run_research_debate":
            if not future_review_id:
                raise ValueError("A saved Future Reviewer report is required for Research Debate.")
            return ResearchDebateService(self.db).run_debate(future_review_id)
        if tool == "simulate_reality":
            if not future_review_id:
                raise ValueError("A saved Future Reviewer report is required for Reality Simulator.")
            return RealitySimulatorService(self.db).run_simulation(future_review_id)
        raise ValueError("Unknown ResearchX tool was rejected.")

    def run(self, request: str, future_review_id: str | None = None) -> dict:
        if future_review_id and not self.db.get(FutureReview, future_review_id):
            raise ValueError("Future Reviewer report not found.")

        run = AgenticWorkflowRun(
            id=str(uuid.uuid4()), user_request=request,
            future_review_id=future_review_id, status="running",
            plan=[], results=[], summary="Workflow started.",
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        try:
            plan = self._plan(request, future_review_id)
            run.plan = plan
            self.db.commit()
            results = []
            for index, step in enumerate(plan, start=1):
                try:
                    output = self._execute_tool(step["tool"], request, future_review_id)
                    results.append({"tool": step["tool"], "status": "completed", "reason": step["reason"], "output": output})
                except Exception as exc:
                    results.append({"tool": step["tool"], "status": "failed", "reason": step["reason"], "error": str(exc)[:1000]})
                run.results = results
                self.db.commit()

            completed = sum(1 for item in results if item["status"] == "completed")
            failed = len(results) - completed
            run.status = (
                "failed" if completed == 0
                else "partial" if failed > 0
                else "completed"
            )
            run.summary = f"ResearchX executed {len(results)} planned step(s): {completed} completed and {failed} failed. Review each tool result below; findings are limited to the uploaded research corpus and available evidence."
            self.db.commit()
            self.db.refresh(run)
            return self._serialize(run)
        except Exception as exc:
            self.db.rollback()
            saved = self.db.get(AgenticWorkflowRun, run.id)
            if saved:
                saved.status = "failed"
                saved.summary = f"Workflow planning or execution failed: {str(exc)[:800]}"
                self.db.commit()
                self.db.refresh(saved)
                return self._serialize(saved)
            raise

    def list_runs(self, limit: int = 20):
        rows = self.db.scalars(select(AgenticWorkflowRun).order_by(AgenticWorkflowRun.created_at.desc()).limit(limit)).all()
        return [self._serialize(row) for row in rows]

    def get_run(self, run_id: str):
        row = self.db.get(AgenticWorkflowRun, run_id)
        return self._serialize(row) if row else None

    @staticmethod
    def _serialize(row):
        return {"id": row.id, "user_request": row.user_request, "future_review_id": row.future_review_id, "status": row.status, "plan": row.plan or [], "results": row.results or [], "summary": row.summary, "created_at": row.created_at.isoformat() if row.created_at else None}
