"""
ChromaDB Vector Store.

Manages document storage and retrieval.
- Each uploaded file gets its own collection (namespaced by file_id).
- A shared "all_docs" collection enables cross-file search.
- Metadata (source, page, chunk_index) is stored with each chunk for citation.

Design: VectorStore is a thin wrapper around ChromaDB.
It uses EmbeddingService for vectorization — the two are decoupled
so we can swap the embedding model without touching the store.
"""

import chromadb
from chromadb.config import Settings as ChromaSettings
from backend.rag.loaders import Document
from backend.rag.embedding import embedding_service
from backend.config import settings
from pathlib import Path

# ChromaDB client — persistent storage
_chroma_client: chromadb.ClientAPI | None = None


def get_chroma_client() -> chromadb.ClientAPI:
    global _chroma_client
    if _chroma_client is None:
        persist_dir = str(Path("./data/chroma").resolve())
        _chroma_client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _chroma_client


class VectorStore:
    """ChromaDB-backed vector store with embedding integration."""

    def __init__(self, collection_name: str = "all_docs"):
        self.client = get_chroma_client()
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(self, documents: list[Document], file_id: str) -> int:
        """
        Add documents to the collection.

        Returns the number of chunks added.
        Each chunk gets a unique ID based on file_id + chunk_index.
        """
        if not documents:
            return 0

        texts = [doc.content for doc in documents]
        metadatas = [{**doc.metadata, "file_id": file_id} for doc in documents]
        ids = [f"{file_id}_{i}" for i in range(len(documents))]

        # Embed all texts in batch
        embeddings = embedding_service.embed(texts)

        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )
        return len(documents)

    def search(
        self,
        query: str,
        top_k: int = 5,
        file_id: str | None = None,
    ) -> list[dict]:
        """
        Search for similar documents.

        Returns list of {content, metadata, score} dicts.
        Optionally filter by file_id.
        """
        query_embedding = embedding_service.embed_query(query)

        where = {"file_id": file_id} if file_id else None

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        items = []
        for i in range(len(results["ids"][0])):
            items.append({
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": 1 - results["distances"][0][i],  # cosine distance → similarity
            })

        return items

    def delete_file(self, file_id: str) -> None:
        """Delete all chunks belonging to a specific file."""
        self.collection.delete(where={"file_id": file_id})

    def list_files(self) -> list[str]:
        """List all unique file_ids in the collection."""
        results = self.collection.get(include=["metadatas"])
        file_ids = set()
        for meta in results["metadatas"]:
            if meta and "file_id" in meta:
                file_ids.add(meta["file_id"])
        return list(file_ids)


# Shared collection for cross-file search
all_docs_store = VectorStore("all_docs")
