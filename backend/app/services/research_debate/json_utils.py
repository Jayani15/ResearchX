
import json
import re
from typing import Any


def parse_llm_json(raw: str) -> dict:
    """Extract a JSON object from an LLM response."""

    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("LLM returned an empty response.")

    cleaned = raw.strip()

    cleaned = re.sub(
        r"^\s*```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s*```\s*$", "", cleaned)

    decoder = json.JSONDecoder()

    for index, char in enumerate(cleaned):
        if char != "{":
            continue

        try:
            result, _ = decoder.raw_decode(cleaned[index:])

            if isinstance(result, dict):
                return result

        except json.JSONDecodeError:
            continue

    raise ValueError(
        "LLM returned malformed or incomplete JSON."
    )


def generate_json(
    llm: Any,
    prompt: str,
    stage: str,
    max_tokens: int = 1200,
    temperature: float = 0.1,
) -> dict:
    """
    Generate JSON with one controlled retry.

    Does not silently repair or invent missing information.
    """

    last_error = None

    for attempt in range(2):
        current_prompt = prompt

        if attempt == 1:
            current_prompt += f"""

IMPORTANT RETRY INSTRUCTION:

Your previous {stage} response was not valid JSON.

Generate the complete response again.

- Return one valid JSON object.
- Use double quotes around every key and string.
- Escape quotation marks inside string values.
- Do not include Markdown code fences.
- Do not include text outside the JSON object.
- Keep the response concise enough to fit the output limit.
- Do not omit required fields.
"""

        raw = llm.generate(
            current_prompt,
            max_completion_tokens=max_tokens,
            temperature=temperature,
        )

        try:
            return parse_llm_json(raw)

        except ValueError as exc:
            last_error = exc

    raise RuntimeError(
        f"{stage} could not produce valid JSON after 2 attempts: "
        f"{last_error}"
    )
