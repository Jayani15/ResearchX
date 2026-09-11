from pathlib import Path

from app.services.ingestion.pdf_loader import extract_pdf_text
from app.services.ingestion.text_cleaner import clean_text
from app.services.nlp.research_analyzer import analyze_research_paper


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = PROJECT_ROOT / "data" / "papers" / "sample.pdf"


def test_nlp_analysis():

    pages = extract_pdf_text(str(PDF_PATH))

    full_text = "\n".join(
        clean_text(page["text"])
        for page in pages
    )

    result = analyze_research_paper(full_text)

    assert result is not None

    assert "sections" in result
    assert "sentences" in result
    assert "tokens" in result
    assert "lemmas" in result
    assert "keywords" in result
    assert "statistics" in result

    assert len(result["sentences"]) > 0
    assert len(result["tokens"]) > 0
    assert len(result["keywords"]) > 0

    print("\n========== NLP ANALYSIS ==========")

    print("\nDetected sections:")
    for section in result["sections"]:
        print(" -", section)

    print("\nTop keywords:")
    for keyword in result["keywords"][:10]:
        print(
            f" - {keyword['keyword']}: "
            f"{keyword['score']}"
        )

    print("\nStatistics:")
    for key, value in result["statistics"].items():
        print(f" - {key}: {value}")