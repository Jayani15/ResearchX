import json
import re
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Claim, ClaimEvidence, Paper, FutureReview
from app.services.llm.llm_service import LLMService
from app.services.research_debate.json_utils import generate_json

class BlueTeamService:
    """Builds an evidence-grounded defence of a research proposal."""

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
                    "Blue Team returned invalid JSON. Please retry."
                )

            result = json.loads(cleaned[start:end + 1])

        if not isinstance(result, dict):
            raise ValueError("Blue Team returned an invalid response.")

        return result

    def _get_research_context(self, review: FutureReview):
        """Retrieve relevant claims, prioritising claims in the saved review."""

        corpus = []

        # First, include claims already referenced by Future Reviewer.
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

        # Fill remaining slots with recent claims from the corpus.
        existing_ids = {
            item["claim_id"] for item in corpus
        }

        remaining = self.MAX_CLAIMS - len(corpus)

        if remaining > 0:
            recent_claims = self.db.scalars(
                select(Claim)
                .order_by(Claim.created_at.desc())
                .limit(self.MAX_CLAIMS)
            ).all()

            for claim in recent_claims:
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

                if len(corpus) >= self.MAX_CLAIMS:
                    break

        return corpus

    def defend_proposal(self, future_review_id: str):
        review = self.db.get(FutureReview, future_review_id)

        if not review:
            raise ValueError(
                "The requested Future Reviewer report was not found."
            )

        corpus = self._get_research_context(review)

        prompt = f"""
You are the BLUE TEAM in ResearchX's academic research debate.

Your role is to DEFEND the proposed research project.

You must construct the strongest reasonable academic argument
in favour of the proposal.

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

Suggested improvements:
{json.dumps(review.improvement_suggestions or [], ensure_ascii=False)}


AVAILABLE RESEARCH EVIDENCE

{json.dumps(corpus, ensure_ascii=False)}


YOUR RESPONSIBILITIES

1. Defend the research idea and explain its potential value.

2. Identify strengths in the proposed methodology.

3. Explain how the proposal could contribute to existing research.

4. Identify feasible ways to address weaknesses raised by
   the previous Future Reviewer report.

5. Explain why the proposed research is worth conducting.

6. Use the supplied research claims to support your arguments
   wherever relevant.

STRICT EVIDENCE RULES

- Use only the supplied corpus for statements about existing research.
- You may use general scientific reasoning to defend the proposal.
- Never invent papers, citations, experimental results or claim IDs.
- Every claim ID must exactly match an ID in the supplied corpus.
- Do not treat a research possibility as an established result.
- Do not hide genuine limitations.
- If the corpus contains insufficient evidence, explicitly state it.
- Do not claim that the proposal is globally novel.
- Be persuasive but academically honest.

Return at most 4 arguments.

RETURN ONLY VALID JSON:

{{
    "position": "The proposal has research potential because ...",
    "arguments": [
        {{
            "title": "Argument title",
            "argument": "Main defence",
            "rationale": "Why this argument is reasonable",
            "claim_ids": [],
            "strength": "high, medium, or low"
        }}
    ],
    "overall_assessment": "Overall Blue Team assessment",
    "supporting_claim_ids": [],
    "confidence": 0.5
}}
"""

        result = generate_json(
            llm=LLMService(),
            prompt=prompt,
            stage="Blue Team",
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
                    "argument": str(item.get("argument", ""))[:1500],
                    "rationale": str(item.get("rationale", ""))[:1500],
                    "claim_ids": validate_ids(
                        item.get("claim_ids", [])
                    ),
                    "strength": str(
                        item.get("strength", "medium")
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