from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, ConfigDict

class AgenticWorkflowRequest(BaseModel):
    request: str = Field(min_length=10, max_length=5000)
    future_review_id: str | None = None

class AgenticWorkflowResponse(BaseModel):
    id: str
    user_request: str
    future_review_id: str | None = None
    status: str
    plan: list[dict[str, Any]] = Field(default_factory=list)
    results: list[dict[str, Any]] = Field(default_factory=list)
    summary: str = ""
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
