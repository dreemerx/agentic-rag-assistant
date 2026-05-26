"""
Retriever — the main RAG retrieval interface.

Orchestrates: vector search → rerank → format results with citations.

The agent calls `retriever.search(query)` and gets back
ranked results with source attribution. It never touches
the vector store or reranker directly.
"""

from backend.rag.vectorstore import all_docs_store, VectorStore
from backend.rag.reranker import reranker_service


class Retriever:
    """High-level retrieval interface combining vector search + reranking."""

    def __init__(self, store: VectorStore | None = None):
        self.store = store or all_docs_store

    async def search(
        self,
        query: str,
        top_k: int = 3,
        file_id: str | None = None,
    ) -> dict:
        """
        Search for relevant documents.

        Returns:
            {
                "results": [
                    {
                        "content": "...",
                        "metadata": {"source": "...", "page": 1, ...},
                        "score": 0.85,
                        "rerank_score": 0.92,
                    },
                    ...
                ],
                "query": "...",
                "total": 3,
            }
        """
        # Step 1: Vector search — retrieve more candidates for reranking
        candidates = self.store.search(query, top_k=top_k * 4, file_id=file_id)

        # Step 2: Rerank to final top_k
        reranked = reranker_service.rerank(query, candidates, top_k=top_k)

        return {
            "results": reranked,
            "query": query,
            "total": len(reranked),
        }


# Shared retriever instance
retriever = Retriever()
