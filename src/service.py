from dataclasses import dataclass

from answer_generator import Answer, AnswerGenerator
from citations import check_citation_ids
from conversation import resolve_question
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

    def ask(self, question, history=None):
        question = question.strip()

        if not question:
            raise ValueError("Question cannot be blank.")

        resolved = resolve_question(self.generator, question, history)
        if resolved.clarification:
            return ServiceResult(
                answer=Answer(status="clarification_needed",
                              answer=resolved.clarification, citation_ids=[]),
                verification=None, sources=[], withheld=False,
            )

        results = self.searcher.search(resolved.question, top_k=3)
        answer = self.generator.generate(resolved.question, results)

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
