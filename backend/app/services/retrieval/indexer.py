from app.services.embeddings.embedding_service import (
    EmbeddingService,
)

from app.services.ingestion.pdf_loader import (
    extract_pdf_text,
)

from app.services.ingestion.text_cleaner import (
    clean_text,
)

from app.services.ingestion.chunker import (
    chunk_text,
)

from app.services.retrieval.vector_store import (
    VectorStore,
)


class PaperIndexer:
    """
    Complete indexing pipeline:

    PDF → Text → Chunks → Embeddings → Vector Store
    """

    def __init__(self):

        self.embedding_service = (
            EmbeddingService()
        )

        self.vector_store = (
            VectorStore()
        )

    def index_pdf(
        self,
        file_path: str,
        paper_id: str,
    ) -> dict:

        # ======================================
        # DUPLICATE CHECK
        # ======================================

        if self.vector_store.paper_exists(
            paper_id
        ):

            stats = self.vector_store.get_paper_stats(
                paper_id
            )

            return {
                "paper_id": paper_id,
                "status": "already_indexed",
                "pages": stats["pages"],
                "chunks": stats["chunks"],
                "vector_count": (
                    self.vector_store.count()
                ),
            }

        # ======================================
        # PDF EXTRACTION
        # ======================================

        pages = extract_pdf_text(
            file_path
        )

        # ======================================
        # TEXT CLEANING
        # ======================================

        cleaned_pages = []

        for page in pages:

            cleaned_pages.append(
                {
                    "page_number":
                        page["page_number"],

                    "text":
                        clean_text(
                            page["text"]
                        ),
                }
            )

        # ======================================
        # CHUNKING
        # ======================================

        chunks = chunk_text(
            cleaned_pages
        )

        if not chunks:

            raise ValueError(
                "No text chunks were extracted."
            )

        # ======================================
        # EMBEDDINGS
        # ======================================

        texts = [
            chunk["text"]
            for chunk in chunks
        ]

        embeddings = (
            self.embedding_service
            .embed_documents(texts)
        )

        # ======================================
        # VECTOR STORE
        # ======================================

        self.vector_store.add_chunks(
            chunks=chunks,
            embeddings=embeddings,
            paper_id=paper_id,
        )

        # ======================================
        # RESULT
        # ======================================

        return {
            "paper_id": paper_id,
            "status": "indexed",
            "pages": len(pages),
            "chunks": len(chunks),
            "vector_count": (
                self.vector_store.count()
            ),
        }