from collections import Counter
import re
import numpy as np
from app.services.embeddings.embedding_service import EmbeddingService


def _tokens(text: str) -> set[str]:
    return {
        token for token in re.findall(r"[a-zA-Z0-9]+", text.lower())
        if len(token) > 2
    }


class ClaimMatcher:
    """Find semantically similar claims from different papers."""

    def __init__(self):
        self.embedder = EmbeddingService()

    def candidate_pairs(self, claims: list[dict], threshold: float = 0.62):
        if len(claims) < 2:
            return []
        texts = [c["claim_text"] for c in claims]
        vectors = np.asarray(self.embedder.embed_documents(texts), dtype=float)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        vectors = vectors / np.maximum(norms, 1e-12)
        similarities = vectors @ vectors.T

        pairs = []
        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                if claims[i]["paper_id"] == claims[j]["paper_id"]:
                    continue
                score = float(similarities[i, j])
                if score >= threshold:
                    pairs.append((claims[i], claims[j], score))
        return sorted(pairs, key=lambda item: item[2], reverse=True)