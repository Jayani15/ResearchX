from pathlib import Path

from app.services.ingestion.pdf_loader import extract_pdf_text
from app.services.ingestion.text_cleaner import clean_text
from app.services.nlp.metadata_extractor import extract_metadata
from app.services.nlp.entity_extractor import extract_entities


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PDF_PATH = (
    PROJECT_ROOT
    / "data"
    / "papers"
    / "sample.pdf"
)


def test_metadata_extraction():

    pages = extract_pdf_text(str(PDF_PATH))

    text = "\n".join(
        clean_text(page["text"])
        for page in pages
    )

    metadata = extract_metadata(text)

    print("\n========== METADATA ==========")

    print("Title:", metadata["title"])
    print("Year:", metadata["year"])
    print("DOI:", metadata["doi"])

    assert metadata is not None
    assert "title" in metadata
    assert "year" in metadata
    assert "doi" in metadata


def test_entity_extraction():

    pages = extract_pdf_text(str(PDF_PATH))

    text = "\n".join(
        clean_text(page["text"])
        for page in pages
    )

    result = extract_entities(text)

    print("\n========== RESEARCH ENTITIES ==========")

    for entity in result["research_entities"][:30]:
        print(
            f"{entity['type']:10} → "
            f"{entity['text']}"
        )

    assert result is not None
    assert "standard_entities" in result
    assert "research_entities" in result
    assert "all_entities" in result