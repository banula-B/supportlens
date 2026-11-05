from sentence_transformers import SentenceTransformer

from main import DOCUMENTS_PATH, load_documents


class SemanticSearch:
    def __init__(self, documents):
        self.documents = documents

        print("Loading embedding model...")
        self.model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2",
            device="cpu",
        )

        texts = [
            document["title"] + " " + document["content"]
            for document in documents
        ]

        print("Creating document embeddings...")
        self.document_embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

    def search(self, question, top_k=2):
        if not question.strip() or top_k <= 0:
            return []

        query_embedding = self.model.encode(
            question,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        scores = self.document_embeddings @ query_embedding

        ranked_indices = scores.argsort()[::-1][:top_k]

        return [
            {
                "document": self.documents[int(index)],
                "score": float(scores[index]),
            }
            for index in ranked_indices
        ]


def main():
    documents = load_documents(DOCUMENTS_PATH)
    searcher = SemanticSearch(documents)

    print("\nSemantic search is ready. Type 'exit' to quit.")

    while True:
        question = input("\nQuestion: ").strip()

        if question.lower() == "exit":
            break

        if not question:
            print("Please enter a question.")
            continue

        for result in searcher.search(question):
            document = result["document"]

            print(f"\nTitle: {document['title']}")
            print(f"Similarity: {result['score']:.3f}")
            print(f"Passage: {document['content']}")
            print(f"Source: {document['source']}")


if __name__ == "__main__":
    main()