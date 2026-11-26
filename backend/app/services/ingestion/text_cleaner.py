import re


def clean_text(text: str) -> str:
    """Clean PDF text while preserving paragraph and line boundaries."""
    if not text:
        return ""

    # Normalize line endings, remove control characters, and collapse spaces
    # within each line without flattening section headings into paragraphs.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\t\f\v]+", " ", text)
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)
    return text.strip()