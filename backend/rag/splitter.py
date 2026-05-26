"""
Text Splitter.

V1 uses RecursiveCharacterTextSplitter from langchain-text-splitters.
The splitter is configured with sensible defaults for Chinese + English mixed text.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.rag.loaders import Document


def split_documents(
    documents: list[Document],
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> list[Document]:
    """
    Split a list of Documents into smaller chunks.

    Each chunk inherits the metadata of its parent document,
    plus a chunk_index for ordering within the source.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", ".", " ", ""],
    )

    chunks: list[Document] = []
    for doc in documents:
        texts = splitter.split_text(doc.content)
        for i, text in enumerate(texts):
            metadata = {**doc.metadata, "chunk_index": i}
            chunks.append(Document(content=text, metadata=metadata))

    return chunks
