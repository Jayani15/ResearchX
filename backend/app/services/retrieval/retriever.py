from app.services.embeddings.embedding_service import (
    EmbeddingService,
)

from app.services.retrieval.vector_store import (
    VectorStore,
)


class ResearchRetriever:
    """
    Semantic retriever for research papers.
    """

    def __init__(self):

        self.embedding_service = (
            EmbeddingService()
        )

        self.vector_store = (
            VectorStore()
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:

        if not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        query_embedding = (
            self.embedding_service
            .embed_text(query)
        )

        return self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
        )