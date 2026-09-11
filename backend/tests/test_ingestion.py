from pathlib import Path

from app.services.ingestion.pdf_loader import extract_pdf_text
from app.services.ingestion.text_cleaner import clean_text
from app.services.ingestion.chunker import chunk_text


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = PROJECT_ROOT / "data" / "papers" / "sample.pdf"


def test_ingestion():

    pages = extract_pdf_text(str(PDF_PATH))

    assert len(pages) > 0

    cleaned_pages = []

    for page in pages:
        cleaned_pages.append(
            {
                "page_number": page["page_number"],
                "text": clean_text(page["text"]),
            }
        )

    chunks = chunk_text(cleaned_pages)

    assert len(chunks) > 0

    print(f"\nPages extracted: {len(pages)}")
    print(f"Chunks generated: {len(chunks)}")