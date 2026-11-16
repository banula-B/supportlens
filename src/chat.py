import re

from answer_generator import AnswerGenerator
from hybrid_search import HybridSearch
from main import DOCUMENTS_PATH, load_documents


def check_citation_ids(answer, results):
    allowed_ids = {
        result["document"]["id"] for result in results
    }
    declared_ids = set(answer.citation_ids)
    inline_ids = set(re.findall(r"\[(doc-[^\]\s]+)\]", answer.answer))

    if not declared_ids.issubset(allowed_ids):
        raise ValueError("Answer cites a document that was not retrieved.")

    if inline_ids != declared_ids:
        raise ValueError("Inline citations and citation_ids do not match.")

    if answer.status == "answered" and not declared_ids:
        raise ValueError("An answered response must include a citation.")


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

            print("\nCitation IDs checked; claim support is not verified.")

    finally:
        generator.close()


if __name__ == "__main__":
    main()