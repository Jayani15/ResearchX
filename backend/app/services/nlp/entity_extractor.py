import re
import spacy


nlp = spacy.load("en_core_web_sm")


# Common research terminology patterns.
RESEARCH_PATTERNS = {
    "dataset": [
        r"\b[A-Z][A-Za-z0-9-]{2,}(?:\s+dataset)\b",
        r"\b[A-Z][A-Za-z0-9-]{2,}(?:\s+corpus)\b",
        r"\b[A-Z][A-Za-z0-9-]{2,}(?:\s+benchmark)\b",
    ],

    "metric": [
        r"\baccuracy\b",
        r"\bprecision\b",
        r"\brecall\b",
        r"\bf1[- ]?score\b",
        r"\bf1\b",
        r"\bBLEU\b",
        r"\bROUGE(?:-[0-9]+)?\b",
        r"\bperplexity\b",
        r"\bAUC\b",
        r"\bMAP\b",
    ],

    "model": [
        r"\bBERT\b",
        r"\bRoBERTa\b",
        r"\bALBERT\b",
        r"\bDistilBERT\b",
        r"\bGPT(?:-[0-9.]+)?\b",
        r"\bT5\b",
        r"\bLSTM\b",
        r"\bGRU\b",
        r"\bCNN\b",
        r"\bRNN\b",
        r"\bTransformer\b",
        r"\bResNet(?:-[0-9]+)?\b",
    ],

    "method": [
        r"\bTF-IDF\b",
        r"\bword2vec\b",
        r"\bDoc2Vec\b",
        r"\bBM25\b",
        r"\bNaive Bayes\b",
        r"\bLogistic Regression\b",
        r"\bRandom Forest\b",
        r"\bSupport Vector Machine\b",
        r"\bSVM\b",
        r"\bK-means\b",
        r"\bCRF\b",
    ],
}


def extract_spacy_entities(text: str) -> list[dict]:
    """
    Extract standard named entities using spaCy.
    """

    doc = nlp(text)

    entities = []

    for entity in doc.ents:
        entities.append(
            {
                "text": entity.text,
                "label": entity.label_,
                "start": entity.start_char,
                "end": entity.end_char,
            }
        )

    return entities


def extract_research_entities(text: str) -> list[dict]:
    """
    Extract research-specific entities using pattern matching.
    """

    entities = []

    for entity_type, patterns in RESEARCH_PATTERNS.items():

        for pattern in patterns:

            matches = re.finditer(
                pattern,
                text,
                re.IGNORECASE,
            )

            for match in matches:

                entities.append(
                    {
                        "text": match.group(0),
                        "type": entity_type,
                        "start": match.start(),
                        "end": match.end(),
                    }
                )

    return entities


def remove_duplicate_entities(
    entities: list[dict],
) -> list[dict]:
    """
    Remove duplicate entity spans.
    """

    unique = {}

    for entity in entities:

        key = (
            entity["start"],
            entity["end"],
        )

        unique[key] = entity

    return list(unique.values())


def extract_entities(text: str) -> dict:
    """
    Complete research entity extraction pipeline.
    """

    spacy_entities = extract_spacy_entities(text)

    research_entities = extract_research_entities(text)

    all_entities = spacy_entities + research_entities

    all_entities = remove_duplicate_entities(
        all_entities
    )

    return {
        "standard_entities": spacy_entities,
        "research_entities": research_entities,
        "all_entities": all_entities,
    }