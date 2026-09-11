from app.services.llm.llm_service import LLMService
from app.services.retrieval.retriever import ResearchRetriever


class RAGService:
    """
    Retrieval-Augmented Generation service
    for ResearchX.
    """

    def __init__(self):

        self.retriever = ResearchRetriever()
        self.llm = LLMService()

    def answer(
        self,
        question: str,
        top_k: int = 5,
    ) -> dict:
        """
        Retrieve relevant research evidence
        and generate a grounded answer.
        """

        results = self.retriever.retrieve(
            question,
            top_k=top_k,
        )

        if not results:
            return {
                "answer": (
                    "I could not find sufficient "
                    "evidence in the indexed papers "
                    "to answer this question."
                ),
                "sources": [],
            }

        evidence_blocks = []

        for index, result in enumerate(results, start=1):

            evidence_blocks.append(
                f"""
SOURCE {index}
Paper ID: {result["paper_id"]}
Page: {result["page_number"]}

Evidence:
{result["text"]}
"""
            )

        evidence = "\n".join(
            evidence_blocks
        )

        prompt = f"""
Answer the following research question using
ONLY the evidence provided below.

QUESTION:
{question}

EVIDENCE:
{evidence}

Instructions:
1. Give a concise and accurate answer.
2. Do not introduce information not present
   in the evidence.
3. If the evidence does not fully answer the
   question, explicitly state that.
4. Do not invent citations.
5. Base the answer on the supplied evidence.
"""

        answer = self.llm.generate(prompt)

        sources = []

        for result in results:

            sources.append(
                {
                    "paper_id": result["paper_id"],
                    "page_number": result["page_number"],
                    "distance": result["distance"],
                    "text": result["text"],
                }
            )

        return {
            "answer": answer,
            "sources": sources,
        }