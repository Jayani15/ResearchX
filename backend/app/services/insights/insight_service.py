import json
import re
from uuid import uuid4

from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from app.models import Claim, ClaimEvidence, Paper, ResearchInsight
from app.services.llm.llm_service import LLMService
from app.services.research_debate.json_utils import generate_json

class InsightService:
    """Creates evidence-traceable research insights from stored claims."""

    def __init__(self, db: Session):
        self.db = db

    def _claim_corpus(self):
        claims = self.db.scalars(
            select(Claim).order_by(Claim.paper_id, Claim.created_at)
        ).all()

        corpus = []

        for claim in claims:
            paper = self.db.get(Paper, claim.paper_id)

            evidence = self.db.scalars(
                select(ClaimEvidence).where(
                    ClaimEvidence.claim_id == claim.id
                )
            ).all()

            corpus.append({
                "claim_id": claim.id,
                "paper_id": claim.paper_id,
                "paper_name": paper.filename if paper else claim.paper_id,
                "claim_type": claim.claim_type,
                "claim_text": claim.claim_text,
                "conditions": claim.conditions or {},
                "limitations": claim.limitations,
                "evidence": [
                    {
                        "quote": item.quote,
                        "page": item.page_number
                    }
                    for item in evidence
                ],
            })

        return corpus

    @staticmethod
    def _compact_corpus(corpus, insight_type):
        """
        Select a balanced, compact set of claims to reduce
        LLM token consumption.
        """
        from collections import defaultdict

        grouped = defaultdict(list)

        for item in corpus:
            grouped[item["paper_id"]].append(item)

        # Select claims fairly across papers.
        selected = []
        paper_ids = list(grouped.keys())

        max_claims = 18 if insight_type == "blind_spot" else 20
        max_per_paper = 6

        for index in range(max_per_paper):
            for paper_id in paper_ids:
                if index < len(grouped[paper_id]):
                    selected.append(grouped[paper_id][index])

                    if len(selected) >= max_claims:
                        break

            if len(selected) >= max_claims:
                break

        compact = []

        for item in selected:
            compact.append({
                "claim_id": str(item["claim_id"]),
                "paper_id": str(item["paper_id"]),
                "paper_name": item["paper_name"],
                "claim_type": item["claim_type"],
                "claim_text": str(item["claim_text"])[:500],
                "conditions": item["conditions"],
                "limitations": str(item["limitations"] or "")[:200],
            })

        return compact

    @staticmethod
    def _parse_json(raw: str):
        cleaned = raw.strip()

        cleaned = re.sub(
            r"^```(?:json)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE
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
                "The model did not return valid JSON. Please retry."
            )

    def _generate(  
        self,
        insight_type: str,
        instruction: str,
        minimum_claims: int
    ):
        corpus = self._claim_corpus()

        if len(corpus) < minimum_claims:
            raise LookupError(
                f"At least {minimum_claims} extracted claims "
                "are required for this analysis."
            )

        paper_ids = {
            item["paper_id"] for item in corpus
        }

        if insight_type == "serendipity" and len(paper_ids) < 2:
            raise LookupError(
                "Serendipity analysis requires extracted claims "
                "from at least two different papers."
            )

        
        compact_corpus = self._compact_corpus(
            corpus, insight_type
        )

        prompt = f"""
You are ResearchX, a research intelligence assistant.

Analyze ONLY the supplied claims.
Do not invent facts, papers, results, or claim IDs.

TASK:
{instruction}

Return ONLY valid JSON:

{{
  "insights": [
    {{
      "title": "Short title",
      "description": "Specific finding",
      "rationale": "Why the finding matters",
      "supporting_claim_ids": ["exact claim IDs"],
      "suggested_question": "Research question",
      "confidence": 0.0
    }}
  ]
}}

RULES:
- Generate at most 4 insights.
- Use exact claim IDs from the input.
- Each insight must cite 1-4 claims.
- Serendipity insights MUST link claims from at least
  TWO different papers.
- Do not confuse a possible connection with proven evidence.
- Distinguish observations from hypotheses.
- Confidence must be between 0 and 1.
- Return an empty insights array if evidence is insufficient.
- Do not claim that corpus gaps are universal scientific gaps.
- Keep descriptions concise.

CLAIMS:
{json.dumps(compact_corpus, ensure_ascii=False)}
"""

        llm = LLMService()

        parsed = generate_json(
            llm=llm,
            prompt=prompt,
            stage=f"{insight_type} analysis",
            max_tokens=2000,
            temperature=0.1,
        )

        rows = (
            parsed.get("insights", [])
            if isinstance(parsed, dict)
            else []
        )

        valid_ids = {
            str(item["claim_id"]) for item in compact_corpus
        }

        paper_by_claim = {
            str(item["claim_id"]): str(item["paper_id"])
            for item in compact_corpus
        }

        saved = []

        self.db.execute(
            delete(ResearchInsight).where(
                ResearchInsight.insight_type == insight_type
            )
        )

        for row in rows[:6]:
            linked = [
                str(value)
                for value in row.get("supporting_claim_ids", [])
                if str(value) in valid_ids
            ]

            # Serendipity must connect different papers.
            if insight_type == "serendipity":
                linked_papers = {
                    paper_by_claim[claim_id]
                    for claim_id in linked
                }

                if len(linked_papers) < 2:
                    continue

            if not linked:
                continue

            insight = ResearchInsight(
                id=str(uuid4()),
                insight_type=insight_type,
                title=str(
                    row.get("title", "Research insight")
                )[:300],
                description=str(row.get("description", "")),
                rationale=str(row.get("rationale", "")),
                supporting_claim_ids=linked,
                suggested_question=str(
                    row.get("suggested_question", "")
                ),
                confidence=max(
                    0.0,
                    min(
                        1.0,
                        float(row.get("confidence", 0.5))
                    )
                ),
            )

            self.db.add(insight)
            saved.append(insight)

        self.db.commit()

        return {
            "insight_type": insight_type,
            "insights_generated": len(saved),
            "insights": [
                self._serialize(item) for item in saved
            ]
        }

    def detect_blind_spots(self):
        return self._generate(
            "blind_spot",
            """
            Identify underexplored areas, missing perspectives,
            unreported experimental conditions, assumptions,
            and unanswered questions WITHIN this uploaded paper corpus.

            Do not claim these are universal literature gaps.

            Make each insight actionable and link it to claims
            that reveal the limitation or coverage boundary.
            """,
            minimum_claims=1,
        )

    def discover_serendipity(self):
        return self._generate(
            "serendipity",
            """
            Find unexpected but defensible connections between
            claims from DIFFERENT papers or research areas.

            Prefer cross-domain links that could inspire a new
            hypothesis or method transfer.

            Explain the connection without pretending that
            the papers directly establish it.

            Use claims from at least two distinct paper IDs
            for each insight whenever possible.
            """,
            minimum_claims=2,
        )

    def list_insights(self, insight_type: str | None = None):
        statement = select(ResearchInsight).order_by(
            ResearchInsight.created_at.desc()
        )

        if insight_type:
            statement = statement.where(
                ResearchInsight.insight_type == insight_type
            )

        return [
            self._serialize(item)
            for item in self.db.scalars(statement).all()
        ]

    @staticmethod
    def _serialize(item):
        return {
            "id": item.id,
            "insight_type": item.insight_type,
            "title": item.title,
            "description": item.description,
            "rationale": item.rationale,
            "supporting_claim_ids": (
                item.supporting_claim_ids or []
            ),
            "suggested_question": item.suggested_question,
            "confidence": item.confidence,
            "created_at": (
                item.created_at.isoformat()
                if item.created_at else None
            ),
        }
