import json
import re
from app.services.llm.llm_service import LLMService


ALLOWED_RELATIONSHIPS = {
    "agreement", "true_conflict", "apparent_conflict",
    "complementary", "unrelated", "potential_conflict",
}


class RelationshipClassifier:
    def __init__(self):
        self.llm = LLMService()

    @staticmethod
    def _parse(raw):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
            if not match:
                raise ValueError("Relationship classifier did not return valid JSON.")
            return json.loads(match.group(0))

    def classify(self, claim_a: dict, claim_b: dict, similarity: float) -> dict:
        prompt = f"""
Compare two scientific claims. Use only the supplied claim/evidence/condition data.
Return ONLY JSON:
{{
  "relationship_type": "agreement|true_conflict|apparent_conflict|complementary|unrelated|potential_conflict",
  "explanation": "plain-language explanation",
  "condition_differences": {{
    "dataset": "comparison or not reported",
    "model": "comparison or not reported",
    "metric": "comparison or not reported",
    "sample_size": "comparison or not reported",
    "setting": "comparison or not reported",
    "other": []
  }}
}}

Decision rules:
- agreement: claims support compatible findings.
- true_conflict: claims make incompatible findings under sufficiently comparable reported conditions.
- apparent_conflict: findings differ and one or more material experimental conditions differ.
- potential_conflict: claims appear incompatible, but evidence/conditions are insufficient to establish a true conflict.
- complementary: claims address compatible but different aspects.
- unrelated: not meaningfully about the same question.
- Never assume missing conditions are equal.
- Do not invent values or causal explanations.
- If experimental comparability cannot be established, prefer potential_conflict over true_conflict.
- Clearly distinguish observed condition differences from possible explanations.

Claim A:
{json.dumps(claim_a, ensure_ascii=False)}

Claim B:
{json.dumps(claim_b, ensure_ascii=False)}

Semantic similarity: {similarity:.4f}
"""
        result = self._parse(self.llm.generate(prompt))
        relation = str(result.get("relationship_type", "potential_conflict")).lower()
        if relation not in ALLOWED_RELATIONSHIPS:
            relation = "potential_conflict"
        explanation = str(result.get("explanation", "")).strip()
        if not explanation:
            explanation = "The relationship could not be confidently explained from the available evidence."
        differences = result.get("condition_differences") or {}
        if not isinstance(differences, dict):
            differences = {}
        return {
            "relationship_type": relation,
            "explanation": explanation,
            "condition_differences": differences,
        }