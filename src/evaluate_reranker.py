from time import perf_counter

from evaluate import TEST_CASES
from hybrid_search import HybridSearch
from main import DOCUMENTS_PATH, load_documents
from reranker import Reranker


def main():
    documents = load_documents(DOCUMENTS_PATH)
    hybrid = HybridSearch(documents)
    reranker = Reranker()

    hybrid_hits = 0
    reranked_hits = 0
    candidate_hits = 0
    retrieval_cases = 0
    inspection_cases = 0
    rerank_times = []

    for case in TEST_CASES:
        question = case["question"]
        expected_ids = set(case["expected_ids"])

        # Select up to five candidates for the cross-encoder.
        candidates = hybrid.search(
            question,
            top_k=5,
            candidate_k=10,
        )

        start = perf_counter()
        reranked = reranker.rerank(question, candidates, top_k=1)
        elapsed_ms = (perf_counter() - start) * 1000
        rerank_times.append(elapsed_ms)

        hybrid_id = (
            candidates[0]["document"]["id"] if candidates else None
        )
        reranked_id = (
            reranked[0]["document"]["id"] if reranked else None
        )
        candidate_ids = {
            result["document"]["id"] for result in candidates
        }

        print(f"\nQuestion: {question}")
        print(f"Directly answerable: {case['answerable']}")
        print(f"Hybrid first: {hybrid_id}")
        print(f"Reranked first: {reranked_id}")
        print(f"Reranking time: {elapsed_ms:.1f} ms")

        if reranked:
            print(
                f"Reranker score: "
                f"{reranked[0]['rerank_score']:.3f}"
            )

        if not expected_ids:
            inspection_cases += 1
            print("[INSPECT] No relevant passage is labeled.")
            continue

        retrieval_cases += 1

        candidate_hit = bool(expected_ids & candidate_ids)
        hybrid_hit = hybrid_id in expected_ids
        reranked_hit = reranked_id in expected_ids

        candidate_hits += int(candidate_hit)
        hybrid_hits += int(hybrid_hit)
        reranked_hits += int(reranked_hit)

        print(f"Relevant passage in candidates: {candidate_hit}")
        print(f"Hybrid: {'HIT' if hybrid_hit else 'MISS'}")
        print(f"Reranked: {'HIT' if reranked_hit else 'MISS'}")

    print("\nEvaluation summary")
    print("-" * 45)
    print(
        f"Candidate hit rate @5: "
        f"{candidate_hits}/{retrieval_cases}"
    )
    print(f"Hybrid top-1: {hybrid_hits}/{retrieval_cases}")
    print(f"Reranked top-1: {reranked_hits}/{retrieval_cases}")
    print(f"No-relevant-passage cases inspected: {inspection_cases}")

    if rerank_times:
        mean_ms = sum(rerank_times) / len(rerank_times)
        print(f"Mean reranking time: {mean_ms:.1f} ms")

    print("Timing excludes model loading and hybrid retrieval.")
    print("Timing includes the first inference; this is a rough check.")
    print("Answer support and abstention are not evaluated.")


if __name__ == "__main__":
    main()