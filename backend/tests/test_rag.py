from app.services.rag.rag_service import RAGService


def test_rag():

    rag = RAGService()

    result = rag.answer(
        "What machine learning methods are discussed?",
        top_k=5,
    )

    print("\n========== RAG ==========")

    print("\nAnswer:")
    print(result["answer"])

    print("\nSources:")

    for source in result["sources"]:

        print(
            f"\nPaper: {source['paper_id']}"
        )

        print(
            f"Page: {source['page_number']}"
        )

        print(
            f"Distance: "
            f"{source['distance']:.4f}"
        )

        print(
            f"Text: "
            f"{source['text'][:200]}"
        )

    assert result["answer"]
    assert isinstance(
        result["sources"],
        list,
    )