import re


def clean_text(text: str) -> str:
    """
    Basic cleaning of extracted PDF text.
    """

    if not text:
        return ""

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove spaces before punctuation
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)

    return text.strip()