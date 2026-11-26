import uuid
from sqlalchemy.orm import Session

from app.models import ResearchDebate, FutureReview
from app.services.research_debate.blue_team import BlueTeamService
from app.services.research_debate.red_team import RedTeamService
from app.services.research_debate.judge import JudgeService

class ResearchDebateService:

    def __init__(self, db: Session):
        self.db = db
        self.blue_service = BlueTeamService(db)
        self.red_service = RedTeamService(db)
        self.judge_service = JudgeService(db)

    def run_debate(self, future_review_id: str) -> dict:
        """
        Runs the complete Blue Team vs Red Team debate
        and obtains the Judge's final verdict.
        """

        # 1. Verify that the Future Reviewer report exists.
        review = (
            self.db.query(FutureReview)
            .filter(FutureReview.id == future_review_id)
            .first()
        )

        if not review:
            raise ValueError("Future Reviewer report not found.")

        # 2. Generate the Blue Team defence.
        blue_result = self.blue_service.defend_proposal(
            future_review_id
        )

        # 3. Generate the Red Team challenge.
        red_result = self.red_service.challenge_proposal(
            future_review_id
        )

        # 4. Let the Judge evaluate both teams.
        judge_result = self.judge_service.evaluate(
            future_review_id=future_review_id,
            blue_team=blue_result,
            red_team=red_result,
        )

        # 5. Collect only claim IDs validated by the teams and Judge.
        supporting_ids = set(
            blue_result.get("supporting_claim_ids", [])
        )

        supporting_ids.update(
            red_result.get("supporting_claim_ids", [])
        )

        supporting_ids.update(
            judge_result.get("supporting_claim_ids", [])
        )

        # 6. Create the debate record.
        debate = ResearchDebate(
            id=str(uuid.uuid4()),
            future_review_id=future_review_id,
            blue_team=blue_result,
            red_team=red_result,
            judge_verdict=judge_result,
            supporting_claim_ids=sorted(supporting_ids),
            confidence=judge_result.get("confidence", 0.5),
        )

        # 7. Save the complete debate.
        try:
            self.db.add(debate)
            self.db.commit()
            self.db.refresh(debate)
        except Exception:
            self.db.rollback()
            raise

        return self._serialize(debate)

    def get_debate(self, debate_id: str):
        debate = (
            self.db.query(ResearchDebate)
            .filter(ResearchDebate.id == debate_id)
            .first()
        )

        if not debate:
            return None

        return self._serialize(debate)

    def get_debates(self, limit: int = 20):
        debates = (
            self.db.query(ResearchDebate)
            .order_by(ResearchDebate.created_at.desc())
            .limit(limit)
            .all()
        )

        return [self._serialize(debate) for debate in debates]

    def get_debates_by_review(self, future_review_id: str):
        debates = (
            self.db.query(ResearchDebate)
            .filter(
                ResearchDebate.future_review_id == future_review_id
            )
            .order_by(ResearchDebate.created_at.desc())
            .all()
        )

        return [self._serialize(debate) for debate in debates]

    @staticmethod
    def _serialize(debate: ResearchDebate) -> dict:
        return {
            "id": debate.id,
            "future_review_id": debate.future_review_id,
            "blue_team": debate.blue_team,
            "red_team": debate.red_team,
            "judge_verdict": debate.judge_verdict,
            "supporting_claim_ids": debate.supporting_claim_ids,
            "confidence": debate.confidence,
            "created_at": debate.created_at,
        }
