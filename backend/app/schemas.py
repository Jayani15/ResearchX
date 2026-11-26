from pydantic import BaseModel, Field

class AskRequest(BaseModel):
    question: str
    top_k: int = Field(default=5, ge=1, le=20)

class RelationshipAnalysisRequest(BaseModel):
    similarity_threshold: float = Field(
        default=0.62, ge=0.0, le=1.0
    )
    max_pairs: int = Field(default=100, ge=1, le=500)