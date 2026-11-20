from answer_generator import Answer, AnswerGenerator
from main import DOCUMENTS_PATH, load_documents
from verifier import CitationVerifier


def main():
    documents = load_documents(DOCUMENTS_PATH)
    documents_by_id = {doc["id"]: doc for doc in documents}

    cases = [
        {
            "name": "Correct statement",
            "text": (
                "Resetting your password does not unlock an account "
                "with error AUTH-423 [doc-005]."
            ),
            "citation_ids": ["doc-005"],
            "expected": "supported",
        },
        {
            "name": "Reversed meaning",
            "text": (
                "Resetting your password unlocks an account "
                "with error AUTH-423 [doc-005]."
            ),
            "citation_ids": ["doc-005"],
            "expected": "unsupported",
        },
        {
            "name": "Invented duration",
            "text": (
                "An account with error AUTH-423 automatically unlocks "
                "after 15 minutes [doc-005]."
            ),
            "citation_ids": ["doc-005"],
            "expected": "unsupported",
        },
        {
            "name": "Correct claim with wrong citation",
            "text": (
                "Resetting your password does not unlock an account "
                "with error AUTH-423 [doc-003]."
            ),
            "citation_ids": ["doc-003"],
            "expected": "unsupported",
        },
        {
            "name": "Supported claim plus unsupported addition",
            "text": (
                "Contact the workspace administrator to unlock an "
                "account with error AUTH-423 [doc-005]. "
                "The administrator will respond within five minutes "
                "[doc-005]."
            ),
            "citation_ids": ["doc-005"],
            "expected": "unsupported",
        },
        {
            "name": "Correct paraphrase",
            "text": (
                "For AUTH-423, ask your workspace administrator "
                "to unlock your account [doc-005]."
            ),
            "citation_ids": ["doc-005"],
            "expected": "supported",
        },
    ]

    generator = AnswerGenerator()
    passed = 0

    try:
        verifier = CitationVerifier(generator.client, generator.model)

        for case in cases:
            results = [
                {"document": documents_by_id[document_id]}
                for document_id in case["citation_ids"]
            ]

            draft = Answer(
                status="answered",
                answer=case["text"],
                citation_ids=case["citation_ids"],
            )

            result = verifier.verify(draft, results)
            correct = result.verdict == case["expected"]
            passed += int(correct)

            print(f"\nCase: {case['name']}")
            print(f"Expected: {case['expected']}")
            print(f"Actual: {result.verdict}")
            print(f"Result: {'PASS' if correct else 'FAIL'}")
            print(f"Reason: {result.reason}")

        print(f"\nVerifier checks passed: {passed}/{len(cases)}")

    finally:
        generator.close()


if __name__ == "__main__":
    main()