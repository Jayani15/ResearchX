from app.services.retrieval.retriever import (
    ResearchRetriever,
)


def test_retrieval():

    retriever = ResearchRetriever()

    results = retriever.retrieve(
        "What machine learning methods are discussed?",
        top_k=5,
    )

    print(
        "\n========== RETRIEVAL =========="
    )

    for result in results:

        print(
            "\nPaper:",
            result["paper_id"],
        )

        print(
            "Page:",
            result["page_number"],
        )

        print(
            "Distance:",
            round(
                result["distance"],
                4,
            ),
        )

        print(
            "Text:",
            result["text"][:300],
        )

    assert len(results) > 0