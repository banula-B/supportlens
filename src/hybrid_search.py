from bm25_search import BM25Search
from main import DOCUMENTS_PATH, load_documents
from semantic_search import SemanticSearch


class HybridSearch:
    def __init__(self, documents, rrf_k=60):
        if rrf_k <= 0:
            raise ValueError("rrf_k must be positive.")

        document_ids = [document["id"] for document in documents]

        if len(document_ids) != len(set(document_ids)):
            raise ValueError("Each document must have a unique ID.")

        self.rrf_k = rrf_k
        self.bm25 = BM25Search(documents)
        self.semantic = SemanticSearch(documents)

    def search(self, question, top_k=2, candidate_k=10):
        if not question.strip() or top_k <= 0:
            return []

        if candidate_k < top_k:
            raise ValueError("candidate_k must be at least top_k.")

        rankings = {
            "bm25": self.bm25.search(question, top_k=candidate_k),
            "semantic": self.semantic.search(
                question,
                top_k=candidate_k,
            ),
        }

        combined = {}

        for method, results in rankings.items():
            for rank, result in enumerate(results, start=1):
                document = result["document"]
                document_id = document["id"]

                if document_id not in combined:
                    combined[document_id] = {
                        "document": document,
                        "score": 0.0,
                        "bm25_rank": None,
                        "semantic_rank": None,
                    }

                combined[document_id]["score"] += (
                    1.0 / (self.rrf_k + rank)
                )
                combined[document_id][f"{method}_rank"] = rank

        ranked_results = sorted(
            combined.values(),
            key=lambda result: (
                -result["score"],
                result["document"]["id"],
            ),
        )

        return ranked_results[:top_k]


def main():
    documents = load_documents(DOCUMENTS_PATH)
    searcher = HybridSearch(documents)

    print("\nHybrid search is ready. Type 'exit' to quit.")

    while True:
        question = input("\nQuestion: ").strip()

        if question.lower() == "exit":
            break

        if not question:
            print("Please enter a question.")
            continue

        results = searcher.search(question)

        for position, result in enumerate(results, start=1):
            document = result["document"]

            print(f"\n{position}. {document['title']}")
            print(f"RRF score: {result['score']:.5f}")
            print(f"BM25 rank: {result['bm25_rank']}")
            print(f"Semantic rank: {result['semantic_rank']}")
            print(f"Passage: {document['content']}")
            print(f"Source: {document['source']}")


if __name__ == "__main__":
    main()