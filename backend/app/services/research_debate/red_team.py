import json
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Claim, ClaimEvidence, Paper, FutureReview
from app.services.llm.llm_service import LLMService
from app.services.research_debate.json_utils import generate_json

class RedTeamService:
    """Challenges a research proposal using evidence and critical reasoning."""

    MAX_CLAIMS = 12

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _parse_json(raw: str) -> dict:
        cleaned = raw.strip()

        cleaned = re.sub(
            r"^```(?:json)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            result = json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")

            if start < 0 or end <= start:
                raise ValueError(
                    "Red Team returned invalid JSON. Please retry."
                )

            result = json.loads(cleaned[start:end + 1])

        if not isinstance(result, dict):
            raise ValueError("Red Team returned an invalid response.")

        return result

    def _get_research_context(self, review: FutureReview):
        """Retrieve claims referenced by the review and recent corpus claims."""

        corpus = []
        existing_ids = set()

        # Prioritise evidence already considered by Future Reviewer.
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
                "claim_text": str(claim.claim_text)[:500],
                "conditions": claim.conditions or {},
                "limitations": str(claim.limitations or "")[:200],
                "evidence": (
                    str(evidence.quote)[:200]
                    if evidence else ""
                ),
            })

            existing_ids.add(str(claim.id))

        # Add recent claims to provide a broader critical perspective.
        recent_claims = self.db.scalars(
            select(Claim)
            .order_by(Claim.created_at.desc())
            .limit(self.MAX_CLAIMS)
        ).all()

        for claim in recent_claims:
            if len(corpus) >= self.MAX_CLAIMS:
                break

            if str(claim.id) in existing_ids:
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
                "claim_text": str(claim.claim_text)[:500],
                "conditions": claim.conditions or {},
                "limitations": str(claim.limitations or "")[:200],
                "evidence": (
                    str(evidence.quote)[:200]
                    if evidence else ""
                ),
            })

            existing_ids.add(str(claim.id))

        return corpus

    def challenge_proposal(self, future_review_id: str):
        review = self.db.get(FutureReview, future_review_id)

        if not review:
            raise ValueError(
                "The requested Future Reviewer report was not found."
            )

        corpus = self._get_research_context(review)

        prompt = f"""
You are the RED TEAM in ResearchX's academic research debate.

Your role is to CHALLENGE the proposed research project.

Act as a rigorous, skeptical academic reviewer.
Identify the strongest legitimate reasons why the proposal
may be incomplete, unreliable, difficult to execute,
or insufficiently justified.

RESEARCH PROPOSAL

Title:
{review.research_title}

Research idea:
{review.research_idea}

Proposed methodology:
{review.proposed_methodology or "Not specified"}

Proposed dataset:
{review.proposed_dataset or "Not specified"}

Proposed evaluation metrics:
{review.proposed_metrics or "Not specified"}


PREVIOUS FUTURE REVIEW

Novelty assessment:
{json.dumps(review.novelty_assessment or {}, ensure_ascii=False)}

Methodology review:
{json.dumps(review.methodology_review or {}, ensure_ascii=False)}

Reviewer questions:
{json.dumps(review.reviewer_questions or [], ensure_ascii=False)}

Weaknesses:
{json.dumps(review.weaknesses or [], ensure_ascii=False)}


AVAILABLE RESEARCH EVIDENCE

{json.dumps(corpus, ensure_ascii=False)}


YOUR RESPONSIBILITIES

1. Challenge assumptions made by the research proposal.

2. Identify methodological weaknesses and missing details.

3. Question the suitability of the proposed dataset and metrics.

4. Identify possible threats to validity, reliability and reproducibility.

5. Examine whether the claimed research contribution is
   sufficiently differentiated from the supplied research corpus.

6. Identify contradictions or limitations in the supplied evidence
   when they are genuinely supported by the corpus.

7. Explain what could go wrong if the proposal is implemented
   without addressing these issues.


STRICT EVIDENCE RULES

- Use only the supplied corpus for statements about existing research.
- You may use general scientific reasoning to challenge the proposal.
- Never invent papers, citations, experimental results or claim IDs.
- Every claim ID must exactly match an ID in the supplied corpus.
- Do not manufacture contradictions between unrelated claims.
- Do not assume that missing information proves a method is invalid.
- Distinguish evidence-based criticism from potential risks.
- Do not claim that the proposal is globally non-novel.
- If evidence is insufficient, explicitly acknowledge the limitation.
- Be critical but academically fair.
- Return at most 4 arguments.

RETURN ONLY VALID JSON:

{{
    "position": "The proposal has important unresolved concerns because ...",
    "arguments": [
        {{
            "title": "Challenge title",
            "challenge": "Main criticism",
            "reasoning": "Why this concern matters",
            "claim_ids": [],
            "severity": "high, medium, or low",
            "type": "methodology, novelty, dataset, evaluation, feasibility, or evidence"
        }}
    ],
    "overall_assessment": "Overall Red Team assessment",
    "supporting_claim_ids": [],
    "confidence": 0.5
}}
"""

        result = generate_json(
            llm=LLMService(),
            prompt=prompt,
            stage="Red Team",
            max_tokens=1400,
            temperature=0.1,
        )

        valid_ids = {
            item["claim_id"] for item in corpus
        }

        def validate_ids(values):
            if not isinstance(values, list):
                return []

            return list(dict.fromkeys(
                str(value)
                for value in values
                if str(value) in valid_ids
            ))

        arguments = []

        raw_arguments = result.get("arguments", [])

        if isinstance(raw_arguments, list):
            for item in raw_arguments[:4]:
                if not isinstance(item, dict):
                    continue

                arguments.append({
                    "title": str(item.get("title", ""))[:300],
                    "challenge": str(
                        item.get("challenge", "")
                    )[:1500],
                    "reasoning": str(
                        item.get("reasoning", "")
                    )[:1500],
                    "claim_ids": validate_ids(
                        item.get("claim_ids", [])
                    ),
                    "severity": str(
                        item.get("severity", "medium")
                    ).lower(),
                    "type": str(
                        item.get("type", "evidence")
                    ).lower(),
                })

        supporting_ids = validate_ids(
            result.get("supporting_claim_ids", [])
        )

        for argument in arguments:
            for claim_id in argument["claim_ids"]:
                if claim_id not in supporting_ids:
                    supporting_ids.append(claim_id)

        try:
            confidence = float(result.get("confidence", 0.5))
        except (TypeError, ValueError):
            confidence = 0.5

        confidence = max(0.0, min(1.0, confidence))

        return {
            "position": str(result.get("position", ""))[:1500],
            "arguments": arguments,
            "overall_assessment": str(
                result.get("overall_assessment", "")
            )[:2000],
            "supporting_claim_ids": supporting_ids,
            "confidence": confidence,
            "evidence_available": len(corpus),
        }