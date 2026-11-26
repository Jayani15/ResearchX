import json
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    FutureReview,
    ResearchDebate,
    ResearchRealityAssessment,
    Claim,
    ClaimEvidence,
    Paper,
)
from app.services.llm.llm_service import LLMService
from app.services.research_debate.json_utils import generate_json

class RealitySimulatorService:
    MAX_CLAIMS = 10

    def __init__(self, db: Session):
        self.db = db
        self.llm = LLMService()

    # --------------------------------------------------
    # RESEARCH EVIDENCE
    # --------------------------------------------------

    def _get_research_context(self, review: FutureReview) -> list:
        """Retrieve evidence referenced by Future Reviewer."""

        corpus = []
        seen_ids = set()

        referenced_ids = review.supporting_claim_ids or []

        for claim_id in referenced_ids[:self.MAX_CLAIMS]:
            claim = self.db.get(Claim, claim_id)

            if not claim:
                continue

            paper = self.db.get(Paper, claim.paper_id)

            evidence = self.db.scalars(
                select(ClaimEvidence)
                .where(ClaimEvidence.claim_id == claim.id)
                .limit(1)
            ).first()

            corpus.append({
                "claim_id": str(claim.id),
                "paper_name": (
                    paper.filename if paper else "Unknown paper"
                ),
                "claim_type": claim.claim_type,
                "claim_text": str(claim.claim_text)[:400],
                "limitations": str(claim.limitations or "")[:200],
                "evidence": (
                    str(evidence.quote)[:200]
                    if evidence else ""
                ),
            })

            seen_ids.add(str(claim.id))

        # Fill remaining slots with recent research claims.
        remaining = self.MAX_CLAIMS - len(corpus)

        if remaining > 0:
            recent_claims = self.db.scalars(
                select(Claim)
                .order_by(Claim.created_at.desc())
                .limit(self.MAX_CLAIMS)
            ).all()

            for claim in recent_claims:
                if len(corpus) >= self.MAX_CLAIMS:
                    break

                if str(claim.id) in seen_ids:
                    continue

                paper = self.db.get(Paper, claim.paper_id)

                evidence = self.db.scalars(
                    select(ClaimEvidence)
                    .where(ClaimEvidence.claim_id == claim.id)
                    .limit(1)
                ).first()

                corpus.append({
                    "claim_id": str(claim.id),
                    "paper_name": (
                        paper.filename if paper else "Unknown paper"
                    ),
                    "claim_type": claim.claim_type,
                    "claim_text": str(claim.claim_text)[:400],
                    "limitations": str(claim.limitations or "")[:200],
                    "evidence": (
                        str(evidence.quote)[:200]
                        if evidence else ""
                    ),
                })

                seen_ids.add(str(claim.id))

        return corpus

    # --------------------------------------------------
    # PREVIOUS DEBATE CONTEXT
    # --------------------------------------------------

    def _get_latest_debate(self, review_id: str):
        """Get the latest debate, if one exists."""

        return (
            self.db.query(ResearchDebate)
            .filter(
                ResearchDebate.future_review_id == review_id
            )
            .order_by(ResearchDebate.created_at.desc())
            .first()
        )

    # --------------------------------------------------
    # RUN REALITY SIMULATION
    # --------------------------------------------------

    def run_simulation(self, future_review_id: str) -> dict:
        review = self.db.get(FutureReview, future_review_id)

        if not review:
            raise ValueError("Future Reviewer report not found.")

        corpus = self._get_research_context(review)
        debate = self._get_latest_debate(future_review_id)

        debate_context = {}

        if debate:
            debate_context = {
                "blue_team": debate.blue_team,
                "red_team": debate.red_team,
                "judge_verdict": debate.judge_verdict,
            }

        prompt = f"""
You are the Research Reality Simulator in ResearchX.

Your task is to evaluate whether a research proposal can
realistically be implemented in the real world.

Do not merely judge whether the idea sounds interesting.
Evaluate practical implementation requirements and constraints.

RESEARCH PROPOSAL

Title:
{review.research_title}

Research idea:
{review.research_idea}

Proposed methodology:
{review.proposed_methodology or "Not specified"}

Proposed dataset:
{review.proposed_dataset or "Not specified"}

Proposed metrics:
{review.proposed_metrics or "Not specified"}

FUTURE REVIEWER ASSESSMENT

Novelty:
{json.dumps(review.novelty_assessment or {}, ensure_ascii=False)}

Methodology:
{json.dumps(review.methodology_review or {}, ensure_ascii=False)}

PREVIOUS RESEARCH DEBATE

{json.dumps(debate_context, ensure_ascii=False)}

AVAILABLE RESEARCH EVIDENCE

{json.dumps(corpus, ensure_ascii=False)}

YOUR RESPONSIBILITIES

1. Evaluate technical feasibility.
2. Identify required hardware, software, infrastructure and skills.
3. Estimate implementation and operational costs.
4. Identify privacy, security and ethical concerns.
5. Evaluate dataset availability and accessibility.
6. Identify practical risks and their severity.
7. Recommend realistic mitigation strategies.
8. Give an overall feasibility score between 0 and 1.

IMPORTANT EVIDENCE AND ESTIMATION RULES

- Never invent experimental results or research citations.
- Distinguish facts from assumptions and estimates.
- Do not pretend that an estimated cost is a verified quotation.
- If prices or resource specifications are unavailable,
  state that the estimate is approximate or cannot be determined.
- Do not assume that datasets are publicly accessible.
- Identify missing information explicitly.
- Use supplied claims only for statements about existing research.
- General engineering reasoning may be used for implementation analysis.
- Do not treat missing details as proof that a project is impossible.
- Be realistic, specific and academically responsible.

OUTPUT RULES

Return only one valid JSON object.
No Markdown code fences.
No text outside the JSON object.
Use double quotes for keys and string values.

Use this exact structure:

{{
  "technical_feasibility": {{
    "rating": "high, medium, or low",
    "score": 0.0,
    "explanation": "Technical feasibility explanation",
    "technical_dependencies": [],
    "implementation_challenges": []
  }},
  "resource_requirements": {{
    "hardware": [],
    "software": [],
    "datasets": [],
    "skills": [],
    "infrastructure": []
  }},
  "cost_estimate": {{
    "currency": "INR",
    "estimated_total": null,
    "breakdown": [],
    "assumptions": [],
    "cost_confidence": "low, medium, or high"
  }},
  "privacy_ethics": {{
    "privacy_risks": [],
    "ethical_concerns": [],
    "security_considerations": [],
    "compliance_requirements": []
  }},
  "accessibility": {{
    "dataset_accessibility": "Explanation",
    "infrastructure_accessibility": "Explanation",
    "deployment_constraints": []
  }},
  "risks": [
    {{
      "risk": "Risk description",
      "severity": "high, medium, or low",
      "likelihood": "high, medium, or low",
      "impact": "Potential impact"
    }}
  ],
  "mitigation_strategies": [
    {{
      "risk": "Risk being addressed",
      "strategy": "Mitigation approach",
      "priority": "high, medium, or low"
    }}
  ],
  "overall_assessment": "Overall implementation recommendation",
  "feasibility_score": 0.0,
  "confidence": 0.0
}}

Keep the response concise but sufficiently detailed.
Use null for unknown numerical cost estimates.
Scores must be between 0.0 and 1.0.
"""

        result = generate_json(
            llm=self.llm,
            prompt=prompt,
            stage="Research Reality Simulator",
            max_tokens=2400,
            temperature=0.1,
        )

        # --------------------------------------------------
        # VALIDATE AND NORMALIZE OUTPUT
        # --------------------------------------------------

        def safe_dict(key):
            value = result.get(key, {})
            return value if isinstance(value, dict) else {}

        def safe_list(key):
            value = result.get(key, [])
            return value[:8] if isinstance(value, list) else []

        def safe_score(value, default=0.5):
            try:
                score = float(value)
            except (TypeError, ValueError):
                return default

            if not 0.0 <= score <= 1.0:
                return default

            return score

        technical = safe_dict("technical_feasibility")
        resources = safe_dict("resource_requirements")
        cost = safe_dict("cost_estimate")
        ethics = safe_dict("privacy_ethics")
        accessibility = safe_dict("accessibility")

        # Ensure scores are valid.
        technical["score"] = safe_score(
            technical.get("score")
        )

        feasibility_score = safe_score(
            result.get("feasibility_score")
        )

        confidence = safe_score(
            result.get("confidence")
        )

        # Keep only structured dictionary items in risk lists.
        risks = [
            item for item in safe_list("risks")
            if isinstance(item, dict)
        ]

        mitigation = [
            item for item in safe_list("mitigation_strategies")
            if isinstance(item, dict)
        ]

        # --------------------------------------------------
        # SAVE ASSESSMENT
        # --------------------------------------------------

        assessment = ResearchRealityAssessment(
            id=str(uuid.uuid4()),
            future_review_id=future_review_id,
            technical_feasibility=technical,
            resource_requirements=resources,
            cost_estimate=cost,
            privacy_ethics=ethics,
            accessibility=accessibility,
            risks=risks,
            mitigation_strategies=mitigation,
            overall_assessment=str(
                result.get("overall_assessment", "")
            ),
            feasibility_score=feasibility_score,
            confidence=confidence,
        )

        try:
            self.db.add(assessment)
            self.db.commit()
            self.db.refresh(assessment)

        except Exception:
            self.db.rollback()
            raise

        return self._serialize(assessment)

    # --------------------------------------------------
    # RETRIEVE ASSESSMENTS
    # --------------------------------------------------

    def get_assessment(self, assessment_id: str):
        assessment = self.db.get(
            ResearchRealityAssessment,
            assessment_id,
        )

        if not assessment:
            return None

        return self._serialize(assessment)

    def get_assessments(self, limit: int = 20):
        assessments = (
            self.db.query(ResearchRealityAssessment)
            .order_by(
                ResearchRealityAssessment.created_at.desc()
            )
            .limit(limit)
            .all()
        )

        return [
            self._serialize(item)
            for item in assessments
        ]

    def get_assessments_by_review(self, future_review_id: str):
        assessments = (
            self.db.query(ResearchRealityAssessment)
            .filter(
                ResearchRealityAssessment.future_review_id
                == future_review_id
            )
            .order_by(
                ResearchRealityAssessment.created_at.desc()
            )
            .all()
        )

        return [
            self._serialize(item)
            for item in assessments
        ]

    # --------------------------------------------------
    # SERIALIZATION
    # --------------------------------------------------

    @staticmethod
    def _serialize(assessment):
        return {
            "id": assessment.id,
            "future_review_id": assessment.future_review_id,
            "technical_feasibility": assessment.technical_feasibility,
            "resource_requirements": assessment.resource_requirements,
            "cost_estimate": assessment.cost_estimate,
            "privacy_ethics": assessment.privacy_ethics,
            "accessibility": assessment.accessibility,
            "risks": assessment.risks,
            "mitigation_strategies": assessment.mitigation_strategies,
            "overall_assessment": assessment.overall_assessment,
            "feasibility_score": assessment.feasibility_score,
            "confidence": assessment.confidence,
            "created_at": assessment.created_at,
        }