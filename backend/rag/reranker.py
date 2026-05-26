"""
Reranker Service.

After initial vector search retrieves candidate chunks, the reranker
re-scores them using a cross-encoder model for higher precision.

Default model: BAAI/bge-reranker-v2-m3 — strong Chinese + English performance.
Runs locally — zero API cost.

Why reranking matters:
- Vector search (bi-encoder) is fast but approximate.
- Cross-encoder reranking is slower but much more accurate.
- We retrieve top_k * 4 candidates from vector search, then rerank to top_k.
"""

from sentence_transformers import CrossEncoder
from backend.rag.loaders import Document


class RerankerService:
    """Local reranker using cross-encoder model."""

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or "BAAI/bge-reranker-v2-m3"
        self._model: CrossEncoder | None = None

    def _get_model(self) -> CrossEncoder:
        if self._model is None:
            self._model = CrossEncoder(self.model_name)
        return self._model

    def rerank(
        self,
        query: str,
        documents: list[dict],
        top_k: int = 3,
    ) -> list[dict]:
        """
        Rerank a list of retrieved documents.

        Input: list of {content, metadata, score} dicts from vector search.
        Output: top_k documents re-sorted by cross-encoder score.
        """
        if not documents:
            return []

        model = self._get_model()
        pairs = [(query, doc["content"]) for doc in documents]
        scores = model.predict(pairs)

        # Attach reranker scores and sort
        for doc, score in zip(documents, scores):
            doc["rerank_score"] = float(score)

        reranked = sorted(documents, key=lambda x: x["rerank_score"], reverse=True)
        return reranked[:top_k]


# Singleton — model loaded lazily
reranker_service = RerankerService()
