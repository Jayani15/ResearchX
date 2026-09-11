import re
import spacy


# Load spaCy model once
nlp = spacy.load("en_core_web_sm")


def normalize_text(text: str) -> str:
    """
    Normalize raw research-paper text.
    """

    if not text:
        return ""

    # Replace multiple whitespace characters
    text = re.sub(r"\s+", " ", text)

    # Remove spaces before punctuation
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)

    return text.strip()


def process_text(text: str) -> dict:
    """
    Perform NLP preprocessing on text.

    Returns sentences, tokens and lemmas.
    """

    if not text:
        return {
            "sentences": [],
            "tokens": [],
            "lemmas": [],
        }

    normalized = normalize_text(text)

    doc = nlp(normalized)

    sentences = [
        sentence.text.strip()
        for sentence in doc.sents
        if sentence.text.strip()
    ]

    tokens = [
        token.text
        for token in doc
        if not token.is_space
    ]

    lemmas = [
        token.lemma_.lower()
        for token in doc
        if not token.is_space
        and not token.is_punct
    ]

    return {
        "sentences": sentences,
        "tokens": tokens,
        "lemmas": lemmas,
    }