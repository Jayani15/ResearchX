import os

from groq import Groq


class LLMService:
    """
    LLM interface for ResearchX.

    Uses Groq for LLM inference.
    """

    def __init__(self):

        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("GROQ_MODEL")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is not configured."
            )

        if not model:
            raise ValueError(
                "GROQ_MODEL is not configured."
            )

        self.client = Groq(
            api_key=api_key
        )

        self.model = model

    def generate(
        self,
        prompt: str,
    ) -> str:

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are ResearchX, an "
                        "evidence-grounded research "
                        "assistant. Answer only using "
                        "the supplied evidence. "
                        "Do not use outside knowledge. "
                        "If the evidence is insufficient, "
                        "say so explicitly."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.1,
        )

        return response.choices[0].message.content