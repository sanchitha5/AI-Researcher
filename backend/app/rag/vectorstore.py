"""
ChromaDB vector store.

We keep exactly one Chroma collection ("documents") persisted to
disk at backend/data/chroma/. Every chunk we add carries metadata
(filename, page, chunk_id, document_id) so retrieved results can be
turned directly into citations without a second lookup.

This is intentionally a thin wrapper — students should be able to
read this file top to bottom and understand exactly what's
happening with the vector database.
"""

from functools import lru_cache

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.config import CHROMA_DIR
from app.rag.embeddings import get_embedding_model

COLLECTION_NAME = "documents"


@lru_cache(maxsize=1)
def get_vectorstore() -> Chroma:
    """Return a cached Chroma vector store instance, persisted to disk."""
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embedding_model(),
        persist_directory=str(CHROMA_DIR),
    )


def add_chunks(chunks: list[Document]) -> None:
    """Embed and store a list of chunks in ChromaDB."""
    if not chunks:
        return
    store = get_vectorstore()
    ids = [chunk.metadata["chunk_id"] for chunk in chunks]
    store.add_documents(documents=chunks, ids=ids)


def delete_document(document_id: str) -> None:
    """Remove all chunks belonging to a given document_id from ChromaDB."""
    store = get_vectorstore()
    try:
        store._collection.delete(where={"document_id": document_id})
    except Exception:
        results = store._collection.get(where={"document_id": document_id})
        if results and results.get("ids"):
            store._collection.delete(ids=results["ids"])


def similarity_search(
    query: str, k: int = 5, document_ids: list[str] | None = None
) -> list[Document]:
    """
    Search the vector store for the k most relevant chunks.

    If document_ids is provided, results are restricted to those
    documents only (used when the user selects a subset of files).
    """
    store = get_vectorstore()
    filter_dict = {"document_id": {"$in": document_ids}} if document_ids else None
    return store.similarity_search(query, k=k, filter=filter_dict)


def has_documents() -> bool:
    """Whether the vector store currently contains any chunks at all."""
    store = get_vectorstore()
    return store._collection.count() > 0  # noqa: SLF001 - simplest reliable check
