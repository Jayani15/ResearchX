import json
import re
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import (
    Claim,
    ClaimEvidence,
    Paper,
    FutureReview,
)
from app.services.llm.llm_service import LLMService

class FutureReviewerService:
    """Evidence-grounded AI reviewer for research proposals."""
    MAX_CLAIMS = 15

    def __init__(self, db: Session):
        self.db = db

    def _get_research_context(self):
        claims = self.db.scalars(
            select(Claim)
            .order_by(Claim.created_at.desc())
            .limit(self.MAX_CLAIMS)
        ).all()

        corpus = []

        for claim in claims:
            paper = self.db.get(Paper, claim.paper_id)

            evidence = self.db.scalars(
                select(ClaimEvidence)
                .where(ClaimEvidence.claim_id == claim.id)
                .limit(1)
            ).first()

            corpus.append({
                "claim_id": str(claim.id),
                "paper_id": str(claim.paper_id),
                "paper_name": (
                    paper.filename if paper else "Unknown paper"
                ),
                "claim_type": claim.claim_type,
                "claim_text": str(claim.claim_text)[:600],
                "conditions": claim.conditions or {},
                "limitations": str(claim.limitations or "")[:250],
                "evidence": (
                    str(evidence.quote)[:250]
                    if evidence else ""
                ),
            })

        return corpus

    @staticmethod
    def _parse_json(raw):
        cleaned = raw.strip()

        cleaned = re.sub(
            r"^```(?:json)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            return json.loads(cleaned)

        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")

            if start >= 0 and end > start:
                return json.loads(cleaned[start:end + 1])

            raise ValueError(
                "Future Reviewer returned invalid JSON. Please retry."
            )

    def review_proposal(self, proposal):
        corpus = self._get_research_context()

        research_title = proposal.research_title
        research_idea = proposal.research_idea
        methodology = proposal.proposed_methodology
        dataset = proposal.proposed_dataset
        metrics = proposal.proposed_metrics

        prompt = f"""
You are Future Reviewer, an evidence-grounded academic
research proposal reviewer.

Review the research proposal critically and constructively.

RESEARCH PROPOSAL

Title:
{research_title}

Research idea:
{research_idea}

Proposed methodology:
{methodology or "Not specified"}

Proposed dataset:
{dataset or "Not specified"}

Proposed evaluation metrics:
{metrics or "Not specified"}

AVAILABLE RESEARCH CORPUS:

{json.dumps(corpus, ensure_ascii=False)}

YOUR TASK

1. NOVELTY ASSESSMENT
Evaluate how the proposal relates to the supplied research claims.
Identify similarities and possible differentiation.
Do not claim that an idea is globally novel or not novel.
The uploaded corpus is not the complete scientific literature.

2. METHODOLOGY REVIEW
Evaluate the proposed methodology, feasibility,
experimental design, dataset and evaluation metrics.
Identify missing methodological details.

3. REVIEWER QUESTIONS
Generate challenging but constructive questions
that an academic reviewer may ask.

4. WEAKNESSES
Identify unsupported assumptions, missing experiments,
methodological limitations and evaluation gaps.

5. IMPROVEMENT SUGGESTIONS
Provide specific and actionable improvements.

STRICT RULES

- Use only the supplied corpus for claims about existing research.
- You may critique the proposal using general scientific reasoning.
- Never invent papers, citations, results or claim IDs.
- Cite exact claim IDs when referring to existing research.
- If the corpus does not contain relevant evidence,
  explicitly say that the assessment is limited.
- Distinguish evidence from speculation.
- Do not assume missing information is necessarily a weakness
  if the researcher has not supplied that information.
- Return concise, useful results.
- Return at most 4 reviewer questions.
- Return at most 4 weaknesses.
- Return at most 4 improvement suggestions.
- Confidence must be between 0 and 1.

RETURN ONLY VALID JSON:

{{
  "novelty_assessment": {{
    "assessment": "Detailed assessment",
    "existing_similar_work": [
      {{
        "description": "Related research claim",
        "claim_ids": ["exact claim UUID"]
      }}
    ],
    "differentiation": "Possible differences",
    "potential_novelty": "high, moderate, low, or uncertain"
  }},
  "methodology_review": {{
    "strengths": ["Strength"],
    "concerns": ["Concern"],
    "feasibility": "high, moderate, low, or uncertain",
    "evaluation_review": "Evaluation analysis"
  }},
  "reviewer_questions": [
    {{
      "question": "Question",
      "reason": "Why it matters",
      "severity": "low, medium, or high"
    }}
  ],
  "weaknesses": [
    {{
      "issue": "Issue",
      "explanation": "Explanation",
      "impact": "low, medium, or high",
      "claim_ids": []
    }}
  ],
  "improvement_suggestions": [
    {{
      "suggestion": "Actionable suggestion",
      "expected_benefit": "Expected benefit",
      "priority": "low, medium, or high"
    }}
  ],
  "supporting_claim_ids": [],
  "confidence": 0.5
}}
"""

        raw = LLMService().generate(
            prompt,
            max_completion_tokens=1800,
            temperature=0.1,
        )

        result = self._parse_json(raw)

        if not isinstance(result, dict):
            raise ValueError("Invalid Future Reviewer response.")

        valid_ids = {
            item["claim_id"] for item in corpus
        }

        def validate_claim_ids(values):
            if not isinstance(values, list):
                return []

            return list(dict.fromkeys(
                str(value)
                for value in values
                if str(value) in valid_ids
            ))

        # --------------------------------------------------
        # 4. Validate and sanitize generated sections
        # --------------------------------------------------

        novelty = result.get("novelty_assessment", {})
        methodology_result = result.get("methodology_review", {})

        if not isinstance(novelty, dict):
            novelty = {}

        if not isinstance(methodology_result, dict):
            methodology_result = {}

        similar_work = novelty.get("existing_similar_work", [])

        if not isinstance(similar_work, list):
            similar_work = []

        clean_similar_work = []

        for item in similar_work[:5]:
            if not isinstance(item, dict):
                continue

            clean_similar_work.append({
                "description": str(
                    item.get("description", "")
                )[:1000],
                "claim_ids": validate_claim_ids(
                    item.get("claim_ids", [])
                ),
            })

        novelty["existing_similar_work"] = clean_similar_work

        questions = []
        for item in result.get("reviewer_questions", [])[:4]:
            if isinstance(item, dict):
                questions.append({
                    "question": str(item.get("question", ""))[:1000],
                    "reason": str(item.get("reason", ""))[:1000],
                    "severity": str(
                        item.get("severity", "medium")
                    ).lower(),
                })

        weaknesses = []
        for item in result.get("weaknesses", [])[:4]:
            if isinstance(item, dict):
                weaknesses.append({
                    "issue": str(item.get("issue", ""))[:500],
                    "explanation": str(
                        item.get("explanation", "")
                    )[:1000],
                    "impact": str(
                        item.get("impact", "medium")
                    ).lower(),
                    "claim_ids": validate_claim_ids(
                        item.get("claim_ids", [])
                    ),
                })

        suggestions = []
        for item in result.get(
            "improvement_suggestions", []
        )[:4]:
            if isinstance(item, dict):
                suggestions.append({
                    "suggestion": str(
                        item.get("suggestion", "")
                    )[:1000],
                    "expected_benefit": str(
                        item.get("expected_benefit", "")
                    )[:1000],
                    "priority": str(
                        item.get("priority", "medium")
                    ).lower(),
                })

        supporting_ids = validate_claim_ids(
            result.get("supporting_claim_ids", [])
        )

        # Include valid claim references from related work.
        for item in clean_similar_work:
            for claim_id in item["claim_ids"]:
                if claim_id not in supporting_ids:
                    supporting_ids.append(claim_id)

        try:
            confidence = float(result.get("confidence", 0.5))
        except (TypeError, ValueError):
            confidence = 0.5

        confidence = max(0.0, min(1.0, confidence))

        review = FutureReview(
            id=str(uuid4()),
            research_title=research_title,
            research_idea=research_idea,
            proposed_methodology=methodology,
            proposed_dataset=dataset,
            proposed_metrics=metrics,
            novelty_assessment={
                "assessment": str(
                    novelty.get("assessment", "")
                ),
                "existing_similar_work": clean_similar_work,
                "differentiation": str(
                    novelty.get("differentiation", "")
                ),
                "potential_novelty": str(
                    novelty.get("potential_novelty", "uncertain")
                ),
            },
            methodology_review={
                "strengths": methodology_result.get(
                    "strengths", []
                )[:5],
                "concerns": methodology_result.get(
                    "concerns", []
                )[:5],
                "feasibility": str(
                    methodology_result.get(
                        "feasibility", "uncertain"
                    )
                ),
                "evaluation_review": str(
                    methodology_result.get(
                        "evaluation_review", ""
                    )
                ),
            },
            reviewer_questions=questions,
            weaknesses=weaknesses,
            improvement_suggestions=suggestions,
            supporting_claim_ids=supporting_ids,
            confidence=confidence,
        )

        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)

        return self._serialize(review)

    def list_reviews(self):
        reviews = self.db.scalars(
            select(FutureReview).order_by(
                FutureReview.created_at.desc()
            )
        ).all()

        return {
            "total": len(reviews),
            "reviews": [
                self._serialize(item) for item in reviews
            ],
        }

    def get_review(self, review_id):
        review = self.db.get(FutureReview, review_id)

        if not review:
            return None

        return self._serialize(review)

    @staticmethod
    def _serialize(review):
        return {
            "id": review.id,
            "research_title": review.research_title,
            "research_idea": review.research_idea,
            "proposed_methodology": review.proposed_methodology,
            "proposed_dataset": review.proposed_dataset,
            "proposed_metrics": review.proposed_metrics,
            "novelty_assessment": review.novelty_assessment,
            "methodology_review": review.methodology_review,
            "reviewer_questions": review.reviewer_questions,
            "weaknesses": review.weaknesses,
            "improvement_suggestions": (
                review.improvement_suggestions
            ),
            "supporting_claim_ids": review.supporting_claim_ids,
            "confidence": review.confidence,
            "created_at": (
                review.created_at.isoformat()
                if review.created_at else None
            ),
        }