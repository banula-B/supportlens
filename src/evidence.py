from hybrid_search import HybridSearch
from main import DOCUMENTS_PATH, load_documents


def build_evidence(results):
    """Format retrieved passages with stable citation identifiers."""
    blocks = []

    for result in results:
        document = result["document"]

        blocks.append(
            f"[{document['id']}]\n"
            f"Title: {document['title']}\n"
            f"Source: {document['source']}\n"
            f"Passage: {document['content']}"
        )

    return "\n\n".join(blocks)


def main():
    documents = load_documents(DOCUMENTS_PATH)
    searcher = HybridSearch(documents)

    print("\nEvidence preview is ready. Type 'exit' to quit.")

    while True:
        question = input("\nQuestion: ").strip()

        if question.lower() == "exit":
            break

        if not question:
            print("Please enter a question.")
            continue

        results = searcher.search(question, top_k=3)

        print("\nRetrieved evidence — not a verified answer:\n")
        print(build_evidence(results))


if __name__ == "__main__":
    main()