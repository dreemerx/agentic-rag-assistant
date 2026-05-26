"""
RAG API endpoints.

Handles:
- File upload → parse → chunk → embed → store
- Query retrieval with source citation
- File management (list, delete)
"""

import uuid
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from backend.rag.loaders import get_loader
from backend.rag.splitter import split_documents
from backend.rag.vectorstore import all_docs_store
from backend.rag.retriever import retriever

router = APIRouter(prefix="/rag", tags=["rag"])

# Temp directory for uploaded files
UPLOAD_DIR = Path("./data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class QueryRequest(BaseModel):
    query: str
    top_k: int = 3
    file_id: str | None = None


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a document for RAG indexing.

    Pipeline: save file → load → split → embed → store in ChromaDB.
    Returns file_id for future reference.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Validate file type
    try:
        loader = get_loader(file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Save file
    file_id = str(uuid.uuid4())[:8]
    file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Pipeline: load → split → embed → store
    try:
        documents = await loader.load()
        chunks = split_documents(documents)
        count = all_docs_store.add_documents(chunks, file_id=file_id)
    except Exception as e:
        # Clean up on failure
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")

    return {
        "file_id": file_id,
        "filename": file.filename,
        "chunks_indexed": count,
        "message": f"Successfully indexed {count} chunks",
    }


@router.post("/query")
async def query_documents(request: QueryRequest):
    """
    Query the RAG knowledge base.

    Returns ranked results with source citations.
    """
    results = await retriever.search(
        query=request.query,
        top_k=request.top_k,
        file_id=request.file_id,
    )
    return results


@router.get("/files")
async def list_files():
    """List all indexed files."""
    file_ids = all_docs_store.list_files()
    return {"files": file_ids, "total": len(file_ids)}


@router.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """Delete a file and all its chunks from the index."""
    all_docs_store.delete_file(file_id)
    return {"message": f"Deleted file {file_id}"}
