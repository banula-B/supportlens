from sentence_transformers import CrossEncoder


class Reranker:
    def __init__(self):
        print("Loading cross-encoder reranker...")
        self.model = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L6-v2",
            device="cpu",
            max_length=512,
        )

    def rerank(self, question, candidates, top_k=2):
        if not question.strip() or not candidates or top_k <= 0:
            return []

        pairs = [
            (
                question,
                result["document"]["title"]
                + " "
                + result["document"]["content"],
            )
            for result in candidates
        ]

        scores = self.model.predict(
            pairs,
            batch_size=8,
            show_progress_bar=False,
        )

        reranked = []

        for candidate, score in zip(candidates, scores):
            result = dict(candidate)
            result["rerank_score"] = float(score)
            reranked.append(result)

        reranked.sort(
            key=lambda result: (
                -result["rerank_score"],
                result["document"]["id"],
            )
        )

        return reranked[:top_k]