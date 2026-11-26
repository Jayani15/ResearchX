from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, ConfigDict

class RealitySimulationRequest(BaseModel):
    future_review_id: str = Field(
        min_length=1,
        description="ID of the saved Future Reviewer report",
    )

class RealitySimulationResponse(BaseModel):
    id: str
    future_review_id: str

    technical_feasibility: dict[str, Any]
    resource_requirements: dict[str, Any]
    cost_estimate: dict[str, Any]
    privacy_ethics: dict[str, Any]
    accessibility: dict[str, Any]

    risks: list[dict[str, Any]]
    mitigation_strategies: list[dict[str, Any]]

    overall_assessment: str

    feasibility_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)