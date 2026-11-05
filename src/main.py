import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS_PATH = PROJECT_ROOT / "data" / "documents.json"

STOP_WORDS = {
    "a", "an", "and", "are", "can", "do", "for",
    "how", "i", "in", "is", "it", "my", "of",
    "on", "the", "to", "what", "with",
}


def load_documents(path):
    """Read the support documents from a JSON file."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def tokenize(text):
    """Convert text into a set of searchable words."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return set(words) - STOP_WORDS


def search_documents(question, documents, top_k=2):
    """Rank documents by the number of matching query words."""
    query_words = tokenize(question)
    results = []

    for document in documents:
        searchable_text = document["title"] + " " + document["content"]
        document_words = tokenize(searchable_text)

        matched_words = query_words & document_words
        score = len(matched_words)

        if score > 0:
            results.append({
                "document": document,
                "score": score,
                "matched_words": sorted(matched_words),
            })

    results.sort(key=lambda result: result["score"], reverse=True)
    return results[:top_k]


def main():
    documents = load_documents(DOCUMENTS_PATH)

    print(f"SupportLens loaded {len(documents)} documents.")
    print("Ask a support question, or type 'exit' to quit.")

    while True:
        question = input("\nQuestion: ").strip()

        if question.lower() == "exit":
            print("Goodbye!")
            break

        if not question:
            print("Please enter a question.")
            continue

        results = search_documents(question, documents)

        if not results:
            print("No keyword matches found in the available documents.")
            continue

        for rank, result in enumerate(results, start=1):
            document = result["document"]

            print(f"\n{rank}. {document['title']}")
            print(f"Matching words: {', '.join(result['matched_words'])}")
            print(f"Keyword score: {result['score']}")
            print(f"Passage: {document['content']}")
            print(f"Source: {document['source']}")


if __name__ == "__main__":
    main()