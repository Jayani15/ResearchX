from datetime import datetime, timezone
from sqlalchemy import (
    String,
    Text,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base

def utcnow():
    return datetime.now(timezone.utc)

class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    pages: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    chunks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    claims: Mapped[list["Claim"]] = relationship(
        back_populates="paper",
        cascade="all, delete-orphan",
    )


class Claim(Base):
    __tablename__ = "claims"
    __table_args__ = (
        Index("ix_claims_paper_id", "paper_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    paper_id: Mapped[str] = mapped_column(
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
    )
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[str] = mapped_column(
        String(80), default="finding"
    )
    conditions: Mapped[dict] = mapped_column(
        JSON, default=dict, nullable=False
    )
    limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_chunk_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    paper: Mapped["Paper"] = relationship(back_populates="claims")
    evidence: Mapped[list["ClaimEvidence"]] = relationship(
        back_populates="claim",
        cascade="all, delete-orphan",
    )


class ClaimEvidence(Base):
    __tablename__ = "claim_evidence"
    __table_args__ = (
        UniqueConstraint(
            "claim_id",
            "quote",
            name="uq_claim_evidence_quote",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    claim_id: Mapped[str] = mapped_column(
        ForeignKey("claims.id", ondelete="CASCADE"),
        nullable=False,
    )
    quote: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_id: Mapped[int] = mapped_column(Integer, nullable=False)
    char_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evidence_kind: Mapped[str] = mapped_column(
        String(40), default="supporting_text"
    )

    claim: Mapped["Claim"] = relationship(back_populates="evidence")


class ClaimRelationship(Base):
    __tablename__ = "claim_relationships"
    __table_args__ = (
        UniqueConstraint(
            "source_claim_id",
            "target_claim_id",
            name="uq_claim_relationship_pair",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_claim_id: Mapped[str] = mapped_column(
        ForeignKey("claims.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_claim_id: Mapped[str] = mapped_column(
        ForeignKey("claims.id", ondelete="CASCADE"),
        nullable=False,
    )
    relationship_type: Mapped[str] = mapped_column(
        String(40), nullable=False
    )
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    condition_differences: Mapped[dict] = mapped_column(
        JSON, default=dict, nullable=False
    )
    similarity: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )


class ResearchInsight(Base):
    __tablename__ = "research_insights"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    insight_type: Mapped[str] = mapped_column(
        String(40), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_claim_ids: Mapped[list] = mapped_column(
        JSON, default=list, nullable=False
    )
    suggested_question: Mapped[str] = mapped_column(
        Text, default="", nullable=False
    )
    confidence: Mapped[float] = mapped_column(
        Float, default=0.5, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )


class FutureReview(Base):
    """
    Stores AI-generated reviews of research proposals.
    """

    __tablename__ = "future_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Original researcher input
    research_title: Mapped[str] = mapped_column(
        String(500), nullable=False
    )
    research_idea: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    proposed_methodology: Mapped[str] = mapped_column(
        Text, default="", nullable=False
    )
    proposed_dataset: Mapped[str] = mapped_column(
        Text, default="", nullable=False
    )
    proposed_metrics: Mapped[str] = mapped_column(
        Text, default="", nullable=False
    )

    # Generated review sections
    novelty_assessment: Mapped[dict] = mapped_column(
        JSON, default=dict, nullable=False
    )
    methodology_review: Mapped[dict] = mapped_column(
        JSON, default=dict, nullable=False
    )
    reviewer_questions: Mapped[list] = mapped_column(
        JSON, default=list, nullable=False
    )
    weaknesses: Mapped[list] = mapped_column(
        JSON, default=list, nullable=False
    )
    improvement_suggestions: Mapped[list] = mapped_column(
        JSON, default=list, nullable=False
    )

    # Evidence traceability
    supporting_claim_ids: Mapped[list] = mapped_column(
        JSON, default=list, nullable=False
    )

    confidence: Mapped[float] = mapped_column(
        Float, default=0.5, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

class ResearchDebate(Base):
    """Stores Blue Team vs Red Team research debates and Judge verdicts."""

    __tablename__ = "research_debates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    future_review_id: Mapped[str] = mapped_column(
        ForeignKey("future_reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    blue_team: Mapped[dict] = mapped_column(
        JSON, default=dict, nullable=False
    )

    red_team: Mapped[dict] = mapped_column(
        JSON, default=dict, nullable=False
    )

    judge_verdict: Mapped[dict] = mapped_column(
        JSON, default=dict, nullable=False
    )

    supporting_claim_ids: Mapped[list] = mapped_column(
        JSON, default=list, nullable=False
    )

    confidence: Mapped[float] = mapped_column(
        Float, default=0.5, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

class ResearchRealityAssessment(Base):
    """Stores real-world feasibility assessments of research proposals."""

    __tablename__ = "research_reality_assessments"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    future_review_id: Mapped[str] = mapped_column(
        ForeignKey("future_reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    technical_feasibility: Mapped[dict] = mapped_column(
        JSON, default=dict, nullable=False
    )

    resource_requirements: Mapped[dict] = mapped_column(
        JSON, default=dict, nullable=False
    )

    cost_estimate: Mapped[dict] = mapped_column(
        JSON, default=dict, nullable=False
    )

    privacy_ethics: Mapped[dict] = mapped_column(
        JSON, default=dict, nullable=False
    )

    accessibility: Mapped[dict] = mapped_column(
        JSON, default=dict, nullable=False
    )

    risks: Mapped[list] = mapped_column(
        JSON, default=list, nullable=False
    )

    mitigation_strategies: Mapped[list] = mapped_column(
        JSON, default=list, nullable=False
    )

    overall_assessment: Mapped[str] = mapped_column(
        Text, default="", nullable=False
    )

    feasibility_score: Mapped[float] = mapped_column(
        Float, default=0.5, nullable=False
    )

    confidence: Mapped[float] = mapped_column(
        Float, default=0.5, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )


class AgenticWorkflowRun(Base):
    """Stores plans, tool execution results, and summaries for agentic workflows."""

    __tablename__ = "agentic_workflow_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_request: Mapped[str] = mapped_column(Text, nullable=False)
    future_review_id: Mapped[str | None] = mapped_column(
        ForeignKey("future_reviews.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    plan: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    results: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ResearchWorkspace(Base):
    """A research project workspace grouping papers and generated reports."""
    __tablename__ = "research_workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    research_question: Mapped[str] = mapped_column(Text, default="", nullable=False)
    paper_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ResearchReport(Base):
    """Persisted report snapshot; evidence and AI suggestions remain distinguished."""
    __tablename__ = "research_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("research_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    sections: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    source_manifest: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)