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
        self.client = chromadb.PersistentClient(path=str(path))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks, embeddings, paper_id):
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks and embeddings must match.")
        if not chunks:
            return
        ids, documents, metadatas = [], [], []
        for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            ids.append(f"{paper_id}_chunk_{index}")
            documents.append(chunk["text"])
            metadatas.append({
                "paper_id": paper_id,
                "chunk_id": index,
                "page_number": chunk.get("page_number", -1),
            })
        self.collection.upsert(
            ids=ids, documents=documents,
            embeddings=embeddings, metadatas=metadatas,
        )

    def search(self, query_embedding, top_k=5):
        if top_k < 1:
            raise ValueError("top_k must be at least 1.")
        total = self.collection.count()
        if total == 0:
            return []
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, total),
            include=["documents", "metadatas", "distances"],
        )
        retrieved = []
        for document, metadata, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            retrieved.append({
                "text": document,
                "paper_id": metadata["paper_id"],
                "chunk_id": metadata["chunk_id"],
                "page_number": metadata["page_number"],
                "distance": distance,
            })
        return retrieved

    def get_paper_chunks(self, paper_id: str) -> list[dict]:
        results = self.collection.get(
            where={"paper_id": paper_id},
            include=["documents", "metadatas"],
        )
        chunks = []
        for document, metadata in zip(results["documents"], results["metadatas"]):
            chunks.append({
                "text": document,
                "paper_id": metadata["paper_id"],
                "chunk_id": metadata["chunk_id"],
                "page_number": metadata["page_number"],
            })
        return sorted(chunks, key=lambda item: item["chunk_id"])

    def paper_exists(self, paper_id):
        results = self.collection.get(where={"paper_id": paper_id}, limit=1)
        return bool(results["ids"])

    def get_papers(self):
        results = self.collection.get(include=["metadatas"])
        papers = {}
        for metadata in results["metadatas"]:
            paper_id = metadata["paper_id"]
            papers.setdefault(paper_id, {"paper_id": paper_id, "chunks": 0, "pages": set()})
            papers[paper_id]["chunks"] += 1
            papers[paper_id]["pages"].add(metadata["page_number"])
        return [
            {"paper_id": p["paper_id"], "chunks": p["chunks"], "pages": len(p["pages"])}
            for p in papers.values()
        ]

    def delete_paper(self, paper_id):
        results = self.collection.get(where={"paper_id": paper_id})
        ids = results["ids"]
        if ids:
            self.collection.delete(ids=ids)
        return len(ids)

    def get_paper_stats(self, paper_id):
        chunks = self.get_paper_chunks(paper_id)
        return {
            "paper_id": paper_id,
            "pages": len({c["page_number"] for c in chunks}),
            "chunks": len(chunks),
        }

    def count(self):
        return self.collection.count()
