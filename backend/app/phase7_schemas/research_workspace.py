from pydantic import BaseModel, Field
from typing import Optional

class WorkspaceCreate(BaseModel):
    title: str = Field(min_length=3, max_length=300)
    description: str = ""
    research_question: str = ""
    paper_ids: list[str] = []

class WorkspaceUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=300)
    description: Optional[str] = None
    research_question: Optional[str] = None
    paper_ids: Optional[list[str]] = None

class ReportGenerateRequest(BaseModel):
    title: Optional[str] = None
    include_claims: bool = True
    include_insights: bool = True
    include_reviews: bool = True
    include_workflows: bool = True
