from main import DOCUMENTS_PATH, load_documents, search_documents


TEST_CASES = [
    {
        "question": "How do I reset my password?",
        "expected_id": "doc-001",
    },
    {
        "question": "Background jobs are not running",
        "expected_id": "doc-002",
    },
    {
        "question": "Which file types can I upload?",
        "expected_id": "doc-003",
    },
    {
        "question": "Tell me about elephants",
        "expected_id": None,
    },
    {
        "question": "I lost access to my account",
        "expected_id": "doc-001",
    },
    {
        "question": "Does the application support dark mode?",
        "expected_id": None,
    },
        {
        "question": "Does the password reset link expire after 15 minutes?",
        "expected_id": None,
    },
    {
        "question": "Can I upload a file larger than 10 MB?",
        "expected_id": "doc-003",
    },
    {
        "question": "Are uploaded documents encrypted at rest?",
        "expected_id": None,
    },
    {
        "question": "How many times does the worker retry a failed job?",
        "expected_id": None,
    },
]


def evaluate():
    documents = load_documents(DOCUMENTS_PATH)
    passed = 0

    for case in TEST_CASES:
        results = search_documents(
            case["question"],
            documents,
            top_k=1,
        )

        actual_id = results[0]["document"]["id"] if results else None
        correct = actual_id == case["expected_id"]

        if correct:
            passed += 1

        status = "PASS" if correct else "FAIL"

        print(f"\n[{status}] {case['question']}")
        print(f"  Expected: {case['expected_id']}")
        print(f"  Retrieved: {actual_id}")

    total = len(TEST_CASES)
    print(f"\nPassed {passed}/{total} checks ({passed / total:.1%})")


if __name__ == "__main__":
    evaluate()