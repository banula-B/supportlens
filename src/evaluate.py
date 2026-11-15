from main import DOCUMENTS_PATH, load_documents, search_documents


TEST_CASES = [
    {
        "question": "How do I reset my password?",
        "expected_ids": ["doc-001"],
        "answerable": True,
    },
    {
        "question": "Background jobs are not running",
        "expected_ids": ["doc-002"],
        "answerable": True,
    },
    {
        "question": "Which file types can I upload?",
        "expected_ids": ["doc-003", "doc-006"],
        "answerable": True,
    },
    {
        "question": "Tell me about elephants",
        "expected_ids": [],
        "answerable": False,
    },
    {
        "question": "I lost access to my account",
        "expected_ids": ["doc-001", "doc-005"],
        "answerable": False,
    },
    {
        "question": "Does the application support dark mode?",
        "expected_ids": [],
        "answerable": False,
    },
    {
        "question": "Does the password reset link expire after 15 minutes?",
        "expected_ids": ["doc-001", "doc-004"],
        "answerable": False,
    },
    {
        "question": "Can I upload a file larger than 10 MB?",
        "expected_ids": ["doc-003", "doc-007"],
        "answerable": True,
    },
    {
        "question": "Are uploaded documents encrypted at rest?",
        "expected_ids": ["doc-003"],
        "answerable": False,
    },
    {
        "question": "How many times does the worker retry a failed job?",
        "expected_ids": ["doc-002"],
        "answerable": False,
    },
    {
        "question": "What should I do about AUTH-410?",
        "expected_ids": ["doc-004"],
        "answerable": True,
    },
    {
        "question": "Will resetting my password resolve AUTH-423?",
        "expected_ids": ["doc-005"],
        "answerable": True,
    },
    {
        "question": "How do I fix DOC-415?",
        "expected_ids": ["doc-006"],
        "answerable": True,
    },
    {
        "question": "How do I fix DOC-413?",
        "expected_ids": ["doc-007"],
        "answerable": True,
    },
]

def evaluate():
    documents = load_documents(DOCUMENTS_PATH)
    hits = 0
    total = 0

    for case in TEST_CASES:
        results = search_documents(
            case["question"], documents, top_k=1
        )
        actual_id = (
            results[0]["document"]["id"] if results else None
        )

        expected_ids = case["expected_ids"]

        print(f"\nQuestion: {case['question']}")
        print(f"  Acceptable passages: {expected_ids}")
        print(f"  Retrieved: {actual_id}")
        print(f"  Directly answerable: {case['answerable']}")

        if expected_ids:
            total += 1
            hits += int(actual_id in expected_ids)

    print(f"\nKeyword top-1 retrieval hits: {hits}/{total}")
    print("Answer support and abstention are not evaluated.")


if __name__ == "__main__":
    evaluate()