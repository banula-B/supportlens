import re

from rank_bm25 import BM25Okapi

from main import DOCUMENTS_PATH, STOP_WORDS, load_documents


def tokenize_for_bm25(text):
    """Preserve repeated words so BM25 can count their frequency."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [word for word in words if word not in STOP_WORDS]


class BM25Search:
    def __init__(self, documents):
        if not documents:
            raise ValueError("BM25 requires at least one document.")

        self.documents = documents
        self.tokenized_documents = [
            tokenize_for_bm25(
                document["title"] + " " + document["content"]
            )
            for document in documents
        ]

        if not any(self.tokenized_documents):
            raise ValueError("Documents contain no searchable words.")

        self.index = BM25Okapi(self.tokenized_documents)

    def search(self, question, top_k=2):
        query_tokens = tokenize_for_bm25(question)

        if not query_tokens or top_k <= 0:
            return []

        scores = self.index.get_scores(query_tokens)
        query_words = set(query_tokens)

        # Only include documents with an actual keyword overlap.
        candidates = [
            index
            for index, tokens in enumerate(self.tokenized_documents)
            if query_words.intersection(tokens)
        ]

        ranked_indices = sorted(
            candidates,
            key=lambda index: (
                -float(scores[index]),
                self.documents[index]["id"],
            ),
        )

        return [
            {
                "document": self.documents[index],
                "score": float(scores[index]),
            }
            for index in ranked_indices[:top_k]
        ]


def main():
    documents = load_documents(DOCUMENTS_PATH)
    searcher = BM25Search(documents)

    print("BM25 search is ready. Type 'exit' to quit.")

    while True:
        question = input("\nQuestion: ").strip()

        if question.lower() == "exit":
            break

        if not question:
            print("Please enter a question.")
            continue

        results = searcher.search(question)

        if not results:
            print("No keyword matches found.")
            continue

        for result in results:
            document = result["document"]

            print(f"\nTitle: {document['title']}")
            print(f"BM25 score: {result['score']:.3f}")
            print(f"Passage: {document['content']}")
            print(f"Source: {document['source']}")


if __name__ == "__main__":
    main()