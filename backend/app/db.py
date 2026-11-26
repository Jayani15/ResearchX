from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import DATABASE_URL

class Base(DeclarativeBase):
    pass

_engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)

def create_db_and_tables():
    # Import models so SQLAlchemy registers all table definitions.
    from app.models import Paper, Claim, ClaimEvidence, ClaimRelationship, ResearchInsight, FutureReview, ResearchDebate, ResearchRealityAssessment, AgenticWorkflowRun, ResearchWorkspace, ResearchReport  # noqa: F401
    Base.metadata.create_all(bind=_engine)

def get_db():
    create_db_and_tables()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()