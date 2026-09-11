from pathlib import Path

from app.services.embeddings.embedding_service import (
    EmbeddingService,
)

from app.services.retrieval.indexer import (
    PaperIndexer,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PDF_PATH = (
    PROJECT_ROOT
    / "data"
    / "papers"
    / "sample.pdf"
)


def test_embedding():

    service = EmbeddingService()

    embedding = service.embed_text(
        "Natural language processing research."
    )

    print(
        "\nEmbedding dimensions:",
        len(embedding),
    )

    assert len(embedding) > 0


def test_index_pdf():

    indexer = PaperIndexer()

    result = indexer.index_pdf(
        str(PDF_PATH),
        paper_id="sample_paper",
    )

    print("\n========== INDEXING ==========")

    print("Paper ID:", result["paper_id"])
    print("Pages:", result["pages"])
    print("Chunks:", result["chunks"])
    print(
        "Total vectors:",
        result["vector_count"],
    )

    assert result["pages"] > 0
    assert result["chunks"] > 0
    assert result["vector_count"] > 0