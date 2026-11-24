import re

from answer_generator import AnswerGenerator
from hybrid_search import HybridSearch
from main import DOCUMENTS_PATH, load_documents
from verifier import CitationVerifier

generator = AnswerGenerator()
verifier = CitationVerifier(generator.client, generator.model)


def check_citation_ids(answer, results):
    allowed_ids = {
        result["document"]["id"] for result in results
    }

    declared_ids = set(answer.citation_ids)

    inline_ids = set(
        re.findall(r"\[(doc-[^\]\s]+)\]", answer.answer)
    )

    unknown_ids = (declared_ids | inline_ids) - allowed_ids

    if unknown_ids:
        raise ValueError(
            "Answer cites documents that were not retrieved: "
            f"{sorted(unknown_ids)}"
        )

    if inline_ids != declared_ids:
        missing_from_list = inline_ids - declared_ids
        missing_from_text = declared_ids - inline_ids

        raise ValueError(
            "Inline citations and citation_ids do not match.\n"
            f"Inline IDs detected: {sorted(inline_ids)}\n"
            f"Declared IDs: {sorted(declared_ids)}\n"
            f"Missing from citation_ids: {sorted(missing_from_list)}\n"
            f"Missing from answer text: {sorted(missing_from_text)}\n"
            f"Rejected draft: {answer.answer!r}"
        )

    if answer.status == "answered" and not declared_ids:
        raise ValueError(
            "An answered response must include a citation."
        )

def main():
    # Validate API configuration before loading the embedding model.
    generator = AnswerGenerator()

    try:
        documents = load_documents(DOCUMENTS_PATH)
        searcher = HybridSearch(documents)

        print("\nSupportLens is ready. Type 'exit' to quit.")

        while True:
            question = input("\nQuestion: ").strip()

            if question.lower() == "exit":
                break

            if not question:
                continue

            results = searcher.search(question, top_k=3)

            try:
                answer = generator.generate(question, results)
                check_citation_ids(answer, results)
                verification = None

                if answer.status == "answered":
                    verification = verifier.verify(answer, results)

                    if verification.verdict != "supported":
                        print("\nStatus: verification_failed")
                        print(
                            "The draft answer did not pass the evidence "
                            "check, so it has been withheld."
                        )
                        print(f"Check result: {verification.verdict}")
                        print(f"Reason: {verification.reason}")
                        continue
            except Exception as error:
                # Avoid printing request details or credentials.
                print(f"Request failed: {type(error).__name__}")
                print(
                    "Check API access/quota or response validation. "
                    "No answer was displayed."
                )
                continue

            print(f"\nStatus: {answer.status}")
            print(answer.answer)

            if answer.citation_ids:
                print("\nCited sources:")
                cited_ids = set(answer.citation_ids)

                for result in results:
                    document = result["document"]

                    if document["id"] in cited_ids:
                        print(
                            f"[{document['id']}] "
                            f"{document['title']} — {document['source']}"
                        )

            if verification is not None:
                print("\nModel-based claim-support check: passed.")
                print("This check can still make mistakes.")
            else:
                print(
                    "\nCitation IDs checked. Claim-support checking "
                    "was skipped for this non-answer status."
                )

    finally:
        generator.close()


if __name__ == "__main__":
    main()