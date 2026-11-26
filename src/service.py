from dataclasses import dataclass

from answer_generator import Answer, AnswerGenerator
from citations import check_citation_ids
from hybrid_search import HybridSearch
from main import DOCUMENTS_PATH, load_documents
from verifier import CitationVerifier, Verification


@dataclass
class ServiceResult:
    # Withheld drafts are not exposed as displayable answers.
    answer: Answer | None
    verification: Verification | None
    sources: list[dict]
    withheld: bool


class SupportLensService:
    def __init__(self):
        self.generator = AnswerGenerator()

        try:
            documents = load_documents(DOCUMENTS_PATH)
            self.searcher = HybridSearch(documents)
            self.verifier = CitationVerifier(
                self.generator.client,
                self.generator.model,
            )
        except Exception:
            self.generator.close()
            raise

    def ask(self, question):
        question = question.strip()

        if not question:
            raise ValueError("Question cannot be blank.")

        results = self.searcher.search(question, top_k=3)
        answer = self.generator.generate(question, results)

        check_citation_ids(answer, results)

        verification = None

        if answer.status == "answered":
            verification = self.verifier.verify(answer, results)

            if verification.verdict != "supported":
                return ServiceResult(
                    answer=None,
                    verification=verification,
                    sources=[],
                    withheld=True,
                )

        cited_ids = set(answer.citation_ids)

        sources = [
            {
                "id": result["document"]["id"],
                "title": result["document"]["title"],
                "source": result["document"]["source"],
            }
            for result in results
            if result["document"]["id"] in cited_ids
        ]

        return ServiceResult(
            answer=answer,
            verification=verification,
            sources=sources,
            withheld=False,
        )

    def close(self):
        self.generator.close()