"""
Embedding Service.

Uses sentence-transformers for local embedding (zero API cost).
Default model: BAAI/bge-m3 — excellent for Chinese + English mixed text.

Design: a single EmbeddingService class that handles both single texts and batches.
The vector store calls this service — the agent never touches embeddings directly.
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from backend.config import settings


class EmbeddingService:
    """Local embedding service using sentence-transformers."""

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or "BAAI/bge-small-zh-v1.5"
        self._model: SentenceTransformer | None = None

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts and return their vectors."""
        model = self._get_model()
        embeddings = model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query text."""
        return self.embed([text])[0]


# Singleton — model is loaded lazily on first use
embedding_service = EmbeddingService()
