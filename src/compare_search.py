from evaluate import TEST_CASES
from hybrid_search import HybridSearch
from main import DOCUMENTS_PATH, load_documents, search_documents


def main():
    documents = load_documents(DOCUMENTS_PATH)

    # HybridSearch already creates both underlying searchers.
    hybrid = HybridSearch(documents)

    methods = {
        "Keyword": lambda question: search_documents(
            question, documents, top_k=1
        ),
        "BM25": lambda question: hybrid.bm25.search(
            question, top_k=1
        ),
        "Semantic": lambda question: hybrid.semantic.search(
            question, top_k=1
        ),
        "Hybrid": lambda question: hybrid.search(
            question, top_k=1
        ),
    }

    hits = {name: 0 for name in methods}
    retrieval_cases = 0
    unsupported_cases = 0

    for case in TEST_CASES:
        question = case["question"]
        expected_ids = case["expected_ids"]

        print(f"\nQuestion: {question}")
        print(f"Directly answerable: {case['answerable']}")

        if expected_ids is None:
            unsupported_cases += 1
            print("Label: insufficient evidence to answer")
        else:
            retrieval_cases += 1
            print(f"Target passage: {expected_ids}")

        for name, search in methods.items():
            results = search(question)
            actual_id = (
                results[0]["document"]["id"]
                if results else None
            )

            if expected_ids is None:
                # A retrieved candidate is not a generated answer.
                print(f"  {name:8}: candidate={actual_id}")
                continue

            correct = actual_id in expected_ids
            hits[name] += int(correct)

            status = "HIT" if correct else "MISS"
            print(f"  {name:8}: {actual_id} [{status}]")

    print("\nTop-1 retrieval results")
    print("-" * 40)

    if retrieval_cases:
        for name, count in hits.items():
            percentage = count / retrieval_cases * 100
            print(
                f"{name:8}: {count}/{retrieval_cases} "
                f"({percentage:.1f}%)"
            )
    else:
        print("No labeled retrieval cases.")

    print(
        f"\nCases with no relevant passage inspected: "
        f"{unsupported_cases}"
    )
    print("Answer support and abstention are not evaluated yet.")


if __name__ == "__main__":
    main()