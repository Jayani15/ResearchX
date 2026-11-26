from app.services.agentic_workflow.service import AgenticWorkflowService

def test_fallback_planner_selects_relevant_tools():
    service = object.__new__(AgenticWorkflowService)
    plan = service._fallback_plan(
        "Compare conflicting claims and identify research gaps", None
    )
    tools = [step["tool"] for step in plan]
    assert "retrieve_research" in tools
    assert "analyze_relationships" in tools
    assert "detect_blind_spots" in tools
    assert "run_research_debate" not in tools

def test_fallback_planner_only_adds_proposal_tools_with_review_id():
    service = object.__new__(AgenticWorkflowService)
    plan = service._fallback_plan(
        "Debate this proposal and assess implementation feasibility", "review-123"
    )
    tools = [step["tool"] for step in plan]
    assert "run_research_debate" in tools
    assert "simulate_reality" in tools
