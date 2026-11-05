from evaluate import TEST_CASES
from main import DOCUMENTS_PATH, load_documents, search_documents
from semantic_search import SemanticSearch


def main():
    documents = load_documents(DOCUMENTS_PATH)
    semantic_searcher = SemanticSearch(documents)

    keyword_hits = 0
    semantic_hits = 0
    relevant_cases = 0

    for case in TEST_CASES:
        question = case["question"]
        expected_id = case["expected_id"]

        keyword_results = search_documents(question, documents, top_k=1)
        semantic_results = semantic_searcher.search(question, top_k=1)

        keyword_id = (
            keyword_results[0]["document"]["id"]
            if keyword_results else None
        )
        semantic_id = (
            semantic_results[0]["document"]["id"]
            if semantic_results else None
        )
        semantic_score = (
            semantic_results[0]["score"]
            if semantic_results else None
        )

        print(f"\nQuestion: {question}")
        print(f"Expected relevant document: {expected_id}")
        print(f"Keyword top result: {keyword_id}")
        print(f"Semantic top result: {semantic_id}")

        if semantic_score is not None:
            print(f"Semantic similarity: {semantic_score:.3f}")

        if expected_id is None:
            print("Unsupported question: inspect the retrieved candidates.")
            continue

        relevant_cases += 1
        keyword_hits += int(keyword_id == expected_id)
        semantic_hits += int(semantic_id == expected_id)

    print("\nTop-1 retrieval hits on questions with a relevant document:")
    print(f"Keyword: {keyword_hits}/{relevant_cases}")
    print(f"Semantic: {semantic_hits}/{relevant_cases}")


if __name__ == "__main__":
    main()