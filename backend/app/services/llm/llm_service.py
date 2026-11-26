import os

class LLMService:
    """LLM interface for ResearchX using Groq inference."""

    def __init__(self):
        # Lazy import keeps utility and unit tests importable.
        try:
            from groq import Groq
        except ImportError as exc:
            raise RuntimeError(
                "Groq SDK is missing. Install backend/requirements.txt."
            ) from exc

        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("GROQ_MODEL")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is not configured in the repository-root .env file."
            )

        if not model:
            raise ValueError(
                "GROQ_MODEL is not configured in the repository-root .env file."
            )

        self.client = Groq(api_key=api_key)
        self.model = model

        # Default output budget for ordinary LLM requests.
        try:
            self.default_max_tokens = int(
                os.getenv("GROQ_MAX_COMPLETION_TOKENS", "2048")
            )
        except ValueError:
            self.default_max_tokens = 2048

    def generate(
        self,
        prompt: str,
        max_completion_tokens: int | None = None,
        temperature: float = 0.1,
        reasoning_effort: str | None = None,
    ) -> str:
        """
        Generate an LLM response.

        Individual services can override the output-token budget.
        """

        token_limit = (
            max_completion_tokens
            if max_completion_tokens is not None
            else self.default_max_tokens
        )

        if token_limit <= 0:
            raise ValueError("Token limit must be greater than zero.")

        request = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are ResearchX, an evidence-grounded research "
                        "assistant. Answer only using the supplied evidence. "
                        "Do not invent facts or citations. If evidence is "
                        "insufficient, say so explicitly."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": temperature,
            "max_completion_tokens": token_limit,
        }

        # Only pass this parameter when explicitly requested.
        if reasoning_effort is not None:
            request["reasoning_effort"] = reasoning_effort

        response = self.client.chat.completions.create(**request)

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError("The LLM returned an empty response.")

        return content.strip()