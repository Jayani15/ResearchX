import re

def normalize_for_match(value: str) -> str:
    value = value.casefold()
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"[^\w%./+-]+", " ", value)
    return value.strip()

def locate_quote(quote: str, source_text: str):
    """
    Verify an extracted quotation against the original extracted PDF text.
    Returns offsets in the original source text when a normalized exact match
    can be located. It intentionally does not accept merely similar wording.
    """
    if not quote or not source_text:
        return None

    # First try exact matching.
    start = source_text.find(quote)
    if start >= 0:
        return start, start + len(quote)

    normalized_quote = normalize_for_match(quote)
    normalized_source = normalize_for_match(source_text)
    if not normalized_quote or normalized_quote not in normalized_source:
        return None

    # The normalized match is accepted as a quote verification, but offsets
    # are omitted because normalization changes character positions.
    return None, None

def quote_is_supported(quote: str, source_text: str) -> bool:
    if not quote or not source_text:
        return False
    return normalize_for_match(quote) in normalize_for_match(source_text)