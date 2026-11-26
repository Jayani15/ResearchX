import json
import re
from uuid import uuid4

from app.services.llm.llm_service import LLMService
from app.services.claims.evidence_validator import locate_quote, quote_is_supported


CLAIM_SCHEMA_INSTRUCTIONS = """
Return ONLY valid JSON with this exact structure:
{
  "claims": [
    {
      "claim": "one concise, checkable scientific statement",
      "claim_type": "finding|method|dataset|limitation|objective|contribution|other",
      "evidence_quote": "an exact verbatim quotation copied from the supplied text",
      "conditions": {
        "dataset": null,
        "model": null,
        "metric": null,
        "sample_size": null,
        "setting": null,
        "other": []
      },
      "limitations": null,
      "confidence": 0.0
    }
  ]
}
Rules:
- Extract only claims explicitly stated in the supplied text.
- Do not infer results, sample sizes, metrics, datasets, or limitations.
- evidence_quote MUST be copied exactly from the supplied text, not paraphrased.
- Use null when a condition is not stated.
- confidence is a number from 0 to 1 reflecting extraction confidence, not truth.
- Return an empty claims array if no checkable claims are present.
- Extract at most 8 high-value claims from this passage.
"""


class ClaimExtractor:
    def __init__(self):
        self.llm = LLMService()

    @staticmethod
    def _parse_json(raw: str) -> dict:
        cleaned = raw.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
            if not match:
                raise ValueError("LLM did not return valid JSON.")
            return json.loads(match.group(0))

    def extract_from_chunk(self, chunk: dict) -> list[dict]:
        text = chunk["text"]
        prompt = (
            "Extract checkable scientific claims from this research-paper passage.\n\n"
            f"{CLAIM_SCHEMA_INSTRUCTIONS}\n"
            f"PAPER ID: {chunk['paper_id']}\n"
            f"PAGE: {chunk['page_number']}\n"
            f"CHUNK ID: {chunk['chunk_id']}\n\n"
            "SOURCE TEXT BEGIN\n"
            f"{text}\n"
            "SOURCE TEXT END"
        )
        parsed = self._parse_json(self.llm.generate(prompt))
        raw_claims = parsed.get("claims", [])
        if not isinstance(raw_claims, list):
            raise ValueError("Invalid claim extraction response: claims must be a list.")

        verified = []
        for item in raw_claims:
            if not isinstance(item, dict):
                continue
            claim_text = str(item.get("claim", "")).strip()
            quote = str(item.get("evidence_quote", "")).strip()
            if not claim_text or not quote_is_supported(quote, text):
                # A claim without a source-verifiable quotation is not stored.
                continue

            start, end = locate_quote(quote, text)
            conditions = item.get("conditions") or {}
            if not isinstance(conditions, dict):
                conditions = {}

            confidence = item.get("confidence")
            try:
                confidence = max(0.0, min(1.0, float(confidence)))
            except (TypeError, ValueError):
                confidence = None

            verified.append({
                "id": str(uuid4()),
                "claim_text": claim_text,
                "claim_type": str(item.get("claim_type") or "other").lower(),
                "evidence_quote": quote,
                "conditions": conditions,
                "limitations": item.get("limitations"),
                "confidence": confidence,
                "source_chunk_id": int(chunk["chunk_id"]),
                "page_number": int(chunk["page_number"]),
                "char_start": start,
                "char_end": end,
            })
        return verified