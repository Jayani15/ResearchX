from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, ConfigDict

class FutureReviewRequest(BaseModel):
    """Research proposal submitted for AI review."""

    research_title: str = Field(
        min_length=5,
        max_length=500,
        description="Title of the proposed research",
    )

    research_idea: str = Field(
        min_length=20,
        max_length=10000,
        description="Description of the research problem and objectives",
    )

    proposed_methodology: str = Field(
        default="",
        max_length=10000,
        description="Proposed research methodology",
    )

    proposed_dataset: str = Field(
        default="",
        max_length=3000,
        description="Dataset or data collection strategy",
    )

    proposed_metrics: str = Field(
        default="",
        max_length=3000,
        description="Evaluation metrics or success criteria",
    )

class NoveltyAssessment(BaseModel):
    assessment: str
    existing_similar_work: list[str] = Field(default_factory=list)
    differentiation: str = ""
    potential_novelty: str = "uncertain"

class MethodologyReview(BaseModel):
    strengths: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    feasibility: str = "uncertain"
    evaluation_review: str = ""

class ReviewerQuestion(BaseModel):
    question: str
    reason: str = ""
    severity: str = "medium"

class Weakness(BaseModel):
    issue: str
    explanation: str = ""
    impact: str = "medium"

class ImprovementSuggestion(BaseModel):
    suggestion: str
    expected_benefit: str = ""
    priority: str = "medium"

class FutureReviewResponse(BaseModel):
    """Complete Future Reviewer output."""

    id: str

    research_title: str
    novelty_assessment: dict[str, Any]
    methodology_review: dict[str, Any]

    reviewer_questions: list[dict[str, Any]]
    weaknesses: list[dict[str, Any]]
    improvement_suggestions: list[dict[str, Any]]

    supporting_claim_ids: list[str] = Field(default_factory=list)

    confidence: float = Field(ge=0.0, le=1.0)

    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class FutureReviewListResponse(BaseModel):
    total: int
    reviews: list[FutureReviewResponse]