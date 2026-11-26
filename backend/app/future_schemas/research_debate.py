from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, ConfigDict


class ResearchDebateRequest(BaseModel):
    future_review_id: str = Field(
        min_length=1,
        description="ID of the saved Future Reviewer report",
    )


class TeamArgument(BaseModel):
    position: str
    arguments: list[dict[str, Any]] = Field(default_factory=list)
    supporting_claim_ids: list[str] = Field(default_factory=list)
    overall_assessment: str = ""


class JudgeVerdict(BaseModel):
    verdict: str
    reasoning: str
    winning_arguments: list[str] = Field(default_factory=list)
    unresolved_risks: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class ResearchDebateResponse(BaseModel):
    id: str
    future_review_id: str
    blue_team: dict[str, Any]
    red_team: dict[str, Any]
    judge_verdict: dict[str, Any]
    supporting_claim_ids: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
