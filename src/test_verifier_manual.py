from answer_generator import Answer, AnswerGenerator
from main import DOCUMENTS_PATH, load_documents
from verifier import CitationVerifier


def main():
    documents = load_documents(DOCUMENTS_PATH)
    document = next(
        doc for doc in documents if doc["id"] == "doc-005"
    )
    results = [{"document": document}]

    cases = [
        (
            "Correct statement",
            "Resetting your password does not unlock an account "
            "with error AUTH-423 [doc-005].",
            "supported",
        ),
        (
            "Reversed meaning",
            "Resetting your password unlocks an account "
            "with error AUTH-423 [doc-005].",
            "unsupported",
        ),
        (
            "Invented duration",
            "An account with error AUTH-423 automatically unlocks "
            "after 15 minutes [doc-005].",
            "unsupported",
        ),
    ]

    generator = AnswerGenerator()

    try:
        verifier = CitationVerifier(generator.client, generator.model)

        for name, text, expected in cases:
            draft = Answer(
                status="answered",
                answer=text,
                citation_ids=["doc-005"],
            )

            result = verifier.verify(draft, results)

            print(f"\nCase: {name}")
            print(f"Expected: {expected}")
            print(f"Actual: {result.verdict}")
            print(f"Reason: {result.reason}")

    finally:
        generator.close()


if __name__ == "__main__":
    main()