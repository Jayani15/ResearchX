from uuid import uuid4
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from app.models import Paper, Claim, ClaimEvidence, ClaimRelationship
from app.services.claims.claim_extractor import ClaimExtractor
from app.services.retrieval.vector_store import VectorStore
from app.services.knowledge_graph.claim_matcher import ClaimMatcher
from app.services.knowledge_graph.relationship_classifier import RelationshipClassifier
from app.services.knowledge_graph.graph_builder import build_claim_graph, graph_to_dict


class ClaimService:
    def __init__(self, db: Session):
        self.db = db
        self.vector_store = VectorStore()

    def register_paper(self, paper_id, filename, sha256, pages, chunks):
        paper = self.db.get(Paper, paper_id)
        if paper is None:
            paper = Paper(
                id=paper_id, filename=filename, sha256=sha256,
                pages=pages, chunks=chunks,
            )
            self.db.add(paper)
        else:
            paper.filename = filename
            paper.pages = pages
            paper.chunks = chunks
        self.db.commit()
        return paper

    def extract_claims(self, paper_id: str, max_chunks: int | None = None):
        paper = self.db.get(Paper, paper_id)
        if paper is None:
            raise LookupError("Paper is not registered in the ResearchX database.")

        chunks = self.vector_store.get_paper_chunks(paper_id)
        if max_chunks is not None:
            chunks = chunks[:max_chunks]
        if not chunks:
            raise LookupError("No indexed chunks found for this paper.")

        # Re-extraction replaces the previous claims and cascades evidence.
        self.db.execute(delete(Claim).where(Claim.paper_id == paper_id))
        self.db.commit()

        extractor = ClaimExtractor()
        created = 0
        rejected = 0
        try:
            for chunk in chunks:
                extracted = extractor.extract_from_chunk(chunk)
                for item in extracted:
                    claim = Claim(
                        id=item["id"],
                        paper_id=paper_id,
                        claim_text=item["claim_text"],
                        claim_type=item["claim_type"],
                        conditions=item["conditions"],
                        limitations=item["limitations"],
                        confidence=item["confidence"],
                        source_chunk_id=item["source_chunk_id"],
                    )
                    evidence = ClaimEvidence(
                        id=str(uuid4()),
                        claim_id=item["id"],
                        quote=item["evidence_quote"],
                        page_number=item["page_number"],
                        chunk_id=item["source_chunk_id"],
                        char_start=item["char_start"],
                        char_end=item["char_end"],
                    )
                    self.db.add(claim)
                    self.db.add(evidence)
                    created += 1
                self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return {
            "paper_id": paper_id,
            "chunks_processed": len(chunks),
            "claims_created": created,
            "note": "Only claims with quotations verifiable against the source chunk are stored.",
        }

    def list_claims(self, paper_id: str | None = None):
        statement = select(Claim)
        if paper_id:
            statement = statement.where(Claim.paper_id == paper_id)
        claims = self.db.scalars(statement.order_by(Claim.created_at)).all()
        output = []
        for claim in claims:
            evidence = self.db.scalars(
                select(ClaimEvidence).where(ClaimEvidence.claim_id == claim.id)
            ).all()
            output.append(self._claim_dict(claim, evidence))
        return output

    @staticmethod
    def _claim_dict(claim, evidence):
        return {
            "id": claim.id,
            "paper_id": claim.paper_id,
            "claim_text": claim.claim_text,
            "claim_type": claim.claim_type,
            "conditions": claim.conditions or {},
            "limitations": claim.limitations,
            "confidence": claim.confidence,
            "source_chunk_id": claim.source_chunk_id,
            "evidence": [
                {
                    "quote": e.quote,
                    "page_number": e.page_number,
                    "chunk_id": e.chunk_id,
                    "char_start": e.char_start,
                    "char_end": e.char_end,
                    "evidence_kind": e.evidence_kind,
                }
                for e in evidence
            ],
        }

    def analyze_relationships(self, threshold=0.62, max_pairs=100):
        claims = self.list_claims()
        if len(claims) < 2:
            return {"candidate_pairs": 0, "relationships_created": 0, "relationships": []}

        matcher = ClaimMatcher()
        pairs = matcher.candidate_pairs(claims, threshold=threshold)[:max_pairs]
        classifier = RelationshipClassifier()
        results = []

        for claim_a, claim_b, similarity in pairs:
            existing = self.db.scalars(
                select(ClaimRelationship).where(
                    ClaimRelationship.source_claim_id == claim_a["id"],
                    ClaimRelationship.target_claim_id == claim_b["id"],
                )
            ).first()
            classified = classifier.classify(claim_a, claim_b, similarity)
            if existing:
                existing.relationship_type = classified["relationship_type"]
                existing.explanation = classified["explanation"]
                existing.condition_differences = classified["condition_differences"]
                existing.similarity = similarity
                relationship = existing
            else:
                relationship = ClaimRelationship(
                    id=str(uuid4()),
                    source_claim_id=claim_a["id"],
                    target_claim_id=claim_b["id"],
                    relationship_type=classified["relationship_type"],
                    explanation=classified["explanation"],
                    condition_differences=classified["condition_differences"],
                    similarity=similarity,
                )
                self.db.add(relationship)
            results.append({
                "id": relationship.id,
                "source_claim_id": claim_a["id"],
                "target_claim_id": claim_b["id"],
                "relationship_type": classified["relationship_type"],
                "explanation": classified["explanation"],
                "condition_differences": classified["condition_differences"],
                "similarity": similarity,
            })

        self.db.commit()
        return {
            "candidate_pairs": len(pairs),
            "relationships_created": len(results),
            "relationships": results,
        }

    def get_graph(self, paper_id: str | None = None):
        claims = self.list_claims(paper_id)
        claim_ids = {claim["id"] for claim in claims}
        statement = select(ClaimRelationship)
        relationships = self.db.scalars(statement).all()
        rel_dicts = []
        for rel in relationships:
            if rel.source_claim_id in claim_ids and rel.target_claim_id in claim_ids:
                rel_dicts.append({
                    "id": rel.id,
                    "source_claim_id": rel.source_claim_id,
                    "target_claim_id": rel.target_claim_id,
                    "relationship_type": rel.relationship_type,
                    "explanation": rel.explanation,
                    "condition_differences": rel.condition_differences or {},
                    "similarity": rel.similarity,
                })
        graph = build_claim_graph(claims, rel_dicts)
        return graph_to_dict(graph)