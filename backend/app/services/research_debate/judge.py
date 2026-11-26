import json
import re
from typing import Any
from sqlalchemy.orm import Session
from app.models import FutureReview
from app.services.llm.llm_service import LLMService
from app.services.research_debate.json_utils import generate_json

class JudgeService:
    MAX_RETRIES = 1
    MAX_OUTPUT_TOKENS = 1800

    def __init__(self, db: Session):
        self.db = db
        self.llm = LLMService()

    # --------------------------------------------------
    # JSON PARSING
    # --------------------------------------------------

    @staticmethod
    def _parse_json(raw: str) -> dict:
        """
        Extract and parse a JSON object from an LLM response.

        Handles:
        - Markdown code fences
        - Additional text before or after JSON
        - JSON objects embedded in explanatory text
        """

        if not isinstance(raw, str) or not raw.strip():
            raise ValueError("Judge returned an empty response.")

        cleaned = raw.strip()

        # Remove markdown code fences.
        cleaned = re.sub(
            r"^\s*```(?:json)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"\s*```\s*$", "", cleaned)

        # First attempt: response is already valid JSON.
        try:
            result = json.loads(cleaned)

            if isinstance(result, dict):
                return result

        except json.JSONDecodeError:
            pass

        # Second attempt: extract a JSON object from surrounding text.
        decoder = json.JSONDecoder()

        for index, character in enumerate(cleaned):
            if character != "{":
                continue

            try:
                result, _ = decoder.raw_decode(cleaned[index:])

                if isinstance(result, dict):
                    return result

            except json.JSONDecodeError:
                continue

        raise ValueError(
            "Judge returned invalid or incomplete JSON. "
            "The response may have been truncated."
        )

    # --------------------------------------------------
    # RESPONSE VALIDATION
    # --------------------------------------------------

    @staticmethod
    def _safe_text(value: Any, default: str = "") -> str:
        if isinstance(value, str):
            return value.strip()

        if value is None:
            return default

        return str(value)

    @staticmethod
    def _safe_list(value: Any, limit: int = 5) -> list[str]:
        if not isinstance(value, list):
            return []

        return [
            item.strip()
            for item in value[:limit]
            if isinstance(item, str) and item.strip()
        ]

    @staticmethod
    def _safe_confidence(value: Any) -> float:
        try:
            confidence = float(value)
        except (TypeError, ValueError):
            return 0.5

        if not 0.0 <= confidence <= 1.0:
            return 0.5

        return confidence

    # --------------------------------------------------
    # JUDGE EVALUATION
    # --------------------------------------------------

    def evaluate(
        self,
        future_review_id: str,
        blue_team: dict,
        red_team: dict,
    ) -> dict:
        """
        Evaluate both debate teams and produce a balanced verdict.

        Retries once if the LLM returns malformed JSON.
        """

        review = (
            self.db.query(FutureReview)
            .filter(FutureReview.id == future_review_id)
            .first()
        )

        if not review:
            raise ValueError("Future Reviewer report not found.")

        # Only use claim IDs validated by the team services.
        valid_claim_ids = set(
            blue_team.get("supporting_claim_ids", [])
        )

        valid_claim_ids.update(
            red_team.get("supporting_claim_ids", [])
        )

        valid_claim_ids = {
            claim_id
            for claim_id in valid_claim_ids
            if isinstance(claim_id, str)
        }

        prompt = f"""
You are the independent Judge in ResearchX Research Debate.

Evaluate the two opposing research teams fairly.

RESEARCH PROPOSAL

Title:
{review.research_title}

Research Idea:
{review.research_idea}

Proposed Methodology:
{review.proposed_methodology}

Proposed Dataset:
{review.proposed_dataset}

Proposed Metrics:
{review.proposed_metrics}

FUTURE REVIEWER ASSESSMENT

Novelty:
{json.dumps(review.novelty_assessment, ensure_ascii=False)}

Methodology:
{json.dumps(review.methodology_review, ensure_ascii=False)}

BLUE TEAM - DEFENCE

{json.dumps(blue_team, ensure_ascii=False)}

RED TEAM - CHALLENGE

{json.dumps(red_team, ensure_ascii=False)}

VALID CLAIM IDS

{json.dumps(sorted(valid_claim_ids))}

YOUR TASK

1. Evaluate the Blue Team's defence.
2. Evaluate the Red Team's criticism.
3. Identify the strongest arguments from both teams.
4. Decide whether the proposal is convincing, promising but
   needs improvement, or currently weak.
5. Identify unresolved risks.
6. Recommend concrete improvements.
7. Distinguish evidence-backed conclusions from assumptions.
8. Do not force a winner when both teams have valid arguments.

STRICT RULES

- Do not invent research papers, citations, results or evidence.
- Only use claim IDs from the VALID CLAIM IDS list.
- Do not treat unsupported arguments as proven.
- Do not claim global novelty or non-novelty.
- A limited uploaded corpus cannot establish global novelty.
- Explicitly acknowledge insufficient evidence.
- Judge the proposal, not the writing quality.
- Be balanced and objective.

OUTPUT REQUIREMENTS

Return exactly ONE valid JSON object.
Do not use Markdown code fences.
Do not include explanations before or after the JSON.
Use double quotes for all JSON keys and string values.
Do not include trailing commas.
Keep the response concise but meaningful.

Use exactly this structure:

{{
  "verdict": "Concise overall verdict",
  "decision": "BLUE_TEAM",
  "reasoning": "Explanation of the decision",
  "blue_team_assessment": "Evaluation of the defence",
  "red_team_assessment": "Evaluation of the criticism",
  "winning_arguments": [
    "Strongest argument and why it matters"
  ],
  "unresolved_risks": [
    "Risk that still needs attention"
  ],
  "recommendations": [
    "Specific research improvement"
  ],
  "evidence_assessment": "Assessment of available evidence",
  "supporting_claim_ids": [],
  "confidence": 0.5
}}

Decision must be exactly one of:
BLUE_TEAM, RED_TEAM, DRAW.

Confidence must be a number between 0.0 and 1.0.

Keep each list to at most four items.
"""

        result = generate_json(
            llm=self.llm,
            prompt=prompt,
            stage="Judge",
            max_tokens=1800,
            temperature=0.0,
        )   

        # --------------------------------------------------
        # VALIDATE DECISION
        # --------------------------------------------------

        decision = str(
            result.get("decision", "DRAW")
        ).strip().upper()

        if decision not in {
            "BLUE_TEAM",
            "RED_TEAM",
            "DRAW",
        }:
            decision = "DRAW"

        # --------------------------------------------------
        # VALIDATE CLAIM IDS
        # --------------------------------------------------

        returned_ids = result.get(
            "supporting_claim_ids", []
        )

        if not isinstance(returned_ids, list):
            returned_ids = []

        validated_ids = sorted({
            claim_id
            for claim_id in returned_ids
            if isinstance(claim_id, str)
            and claim_id in valid_claim_ids
        })

        # --------------------------------------------------
        # BUILD FINAL VERDICT
        # --------------------------------------------------

        return {
            "verdict": self._safe_text(
                result.get("verdict"),
                "No verdict generated.",
            ),

            "decision": decision,

            "reasoning": self._safe_text(
                result.get("reasoning")
            ),

            "blue_team_assessment": self._safe_text(
                result.get("blue_team_assessment")
            ),

            "red_team_assessment": self._safe_text(
                result.get("red_team_assessment")
            ),

            "winning_arguments": self._safe_list(
                result.get("winning_arguments")
            ),

            "unresolved_risks": self._safe_list(
                result.get("unresolved_risks")
            ),

            "recommendations": self._safe_list(
                result.get("recommendations")
            ),

            "evidence_assessment": self._safe_text(
                result.get("evidence_assessment")
            ),

            "supporting_claim_ids": validated_ids,

            "confidence": self._safe_confidence(
                result.get("confidence", 0.5)
            ),
        }