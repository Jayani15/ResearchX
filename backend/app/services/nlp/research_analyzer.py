from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer

from app.services.nlp.preprocessing import process_text
from app.services.nlp.section_detector import split_into_sections
from app.services.nlp.metadata_extractor import extract_metadata
from app.services.nlp.entity_extractor import extract_entities

def extract_keywords(
    text: str,
    top_n: int = 15,
) -> list[dict]:
    """
    Extract important keywords using TF-IDF.
    """

    if not text.strip():
        return []

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=1000,
    )

    matrix = vectorizer.fit_transform([text])

    scores = matrix.toarray()[0]
    features = vectorizer.get_feature_names_out()

    keyword_scores = sorted(
        zip(features, scores),
        key=lambda x: x[1],
        reverse=True,
    )

    return [
        {
            "keyword": keyword,
            "score": round(float(score), 4),
        }
        for keyword, score in keyword_scores[:top_n]
    ]


def calculate_statistics(
    text: str,
    processed: dict,
) -> dict:
    """
    Calculate basic linguistic statistics.
    """

    sentences = processed["sentences"]
    tokens = processed["tokens"]
    lemmas = processed["lemmas"]

    words = [
        token
        for token in tokens
        if any(character.isalpha() for character in token)
    ]

    unique_words = set(
        word.lower()
        for word in words
    )

    return {
        "character_count": len(text),
        "sentence_count": len(sentences),
        "token_count": len(tokens),
        "word_count": len(words),
        "unique_word_count": len(unique_words),
        "average_sentence_length": round(
            len(words) / len(sentences),
            2,
        ) if sentences else 0,
    }


def analyze_research_paper(text: str) -> dict:
    """
    Complete NLP analysis for a research paper.
    """

    processed = process_text(text)

    sections = split_into_sections(text)

    keywords = extract_keywords(text)

    statistics = calculate_statistics(
        text,
        processed,
    )

    metadata = extract_metadata(text)

    entities = extract_entities(text)

    return {
        "metadata": metadata,
        "sections": sections,
        "sentences": processed["sentences"],
        "tokens": processed["tokens"],
        "lemmas": processed["lemmas"],
        "keywords": keywords,
        "statistics": statistics,
        "entities": entities,
    }