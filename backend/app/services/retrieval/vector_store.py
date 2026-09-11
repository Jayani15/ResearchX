from pathlib import Path

import chromadb

from app.config import VECTOR_STORE_DIR


class VectorStore:

    def __init__(
        self,
        persist_directory: str | Path = VECTOR_STORE_DIR,
        collection_name: str = "researchx_papers",
    ):
        path = Path(persist_directory).resolve()
        path.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(path)
        )

        self.collection = (
            self.client.get_or_create_collection(
                name=collection_name,
                metadata={
                    "hnsw:space": "cosine"
                },
            )
        )

    # ==========================================
    # ADD / UPDATE CHUNKS
    # ==========================================

    def add_chunks(
        self,
        chunks: list[dict],
        embeddings: list[list[float]],
        paper_id: str,
    ):
        """
        Store paper chunks and their embeddings.
        """

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Number of chunks and embeddings must match."
            )

        if not chunks:
            return

        ids = []
        documents = []
        metadatas = []

        for index, (chunk, embedding) in enumerate(
            zip(chunks, embeddings)
        ):

            chunk_id = (
                f"{paper_id}_chunk_{index}"
            )

            ids.append(chunk_id)

            documents.append(
                chunk["text"]
            )

            metadatas.append(
                {
                    "paper_id": paper_id,
                    "chunk_id": index,
                    "page_number": chunk.get(
                        "page_number",
                        -1,
                    ),
                }
            )

        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    # ==========================================
    # SEARCH
    # ==========================================

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[dict]:
        """
        Retrieve the most semantically similar chunks.
        """

        if top_k < 1:
            raise ValueError(
                "top_k must be at least 1."
            )

        total = self.collection.count()

        if total == 0:
            return []

        # Never request more results than
        # actually exist in the collection.
        top_k = min(top_k, total)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )

        retrieved = []

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        for document, metadata, distance in zip(
            documents,
            metadatas,
            distances,
        ):

            retrieved.append(
                {
                    "text": document,
                    "paper_id": metadata["paper_id"],
                    "chunk_id": metadata["chunk_id"],
                    "page_number": metadata["page_number"],
                    "distance": distance,
                }
            )

        return retrieved

    # ==========================================
    # PAPER EXISTS
    # ==========================================

    def paper_exists(
        self,
        paper_id: str,
    ) -> bool:
        """
        Check whether a paper has already been indexed.
        """

        results = self.collection.get(
            where={
                "paper_id": paper_id
            },
            limit=1,
        )

        return len(results["ids"]) > 0

    # ==========================================
    # GET ALL PAPERS
    # ==========================================

    def get_papers(self) -> list[dict]:
        """
        Return a unique list of indexed papers.
        """

        total = self.collection.count()

        if total == 0:
            return []

        results = self.collection.get(
            include=[
                "metadatas"
            ]
        )

        papers = {}

        for metadata in results["metadatas"]:

            paper_id = metadata["paper_id"]

            if paper_id not in papers:

                papers[paper_id] = {
                    "paper_id": paper_id,
                    "chunks": 0,
                    "pages": set(),
                }

            papers[paper_id]["chunks"] += 1

            papers[paper_id]["pages"].add(
                metadata["page_number"]
            )

        output = []

        for paper in papers.values():

            output.append(
                {
                    "paper_id": paper["paper_id"],
                    "chunks": paper["chunks"],
                    "pages": len(
                        paper["pages"]
                    ),
                }
            )

        return output

    # ==========================================
    # DELETE PAPER
    # ==========================================

    def delete_paper(
        self,
        paper_id: str,
    ) -> int:
        """
        Delete all chunks belonging to a paper.

        Returns:
            Number of deleted chunks.
        """

        results = self.collection.get(
            where={
                "paper_id": paper_id
            }
        )

        ids = results["ids"]

        if not ids:
            return 0

        self.collection.delete(
            ids=ids
        )

        return len(ids)

    def get_paper_stats(
        self,
        paper_id: str,
    ) -> dict:
        """
        Return statistics for an indexed paper.
        """

        results = self.collection.get(
            where={
                "paper_id": paper_id
            },
            include=[
                "metadatas"
            ],
        )

        metadatas = results["metadatas"]

        if not metadatas:
            return {
                "paper_id": paper_id,
                "pages": 0,
                "chunks": 0,
            }

        pages = set()

        for metadata in metadatas:
            pages.add(
                metadata["page_number"]
            )

        return {
            "paper_id": paper_id,
            "pages": len(pages),
            "chunks": len(metadatas),
        }

    # ==========================================
    # COUNT
    # ==========================================

    def count(self) -> int:
        """
        Return number of stored chunks.
        """

        return self.collection.count()