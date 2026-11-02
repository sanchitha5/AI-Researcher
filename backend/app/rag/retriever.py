"""
Retriever.

A thin convenience layer on top of the vector store that returns
plain dictionaries (instead of LangChain Document objects) so the
rest of the app — especially the LangGraph agent state — doesn't
need to know anything about LangChain's internal types.
"""

from app.rag.vectorstore import similarity_search

TOP_K = 4


def retrieve_document_chunks(
    query: str, document_ids: list[str] | None = None
) -> list[dict]:
    """
    Retrieve the most relevant document chunks for a query.

    Returns a list of dicts like:
        {
            "filename": "paper.pdf",
            "page": 4,
            "chunk_id": "abc123-2",
            "content": "...chunk text...",
        }
    """
    results = similarity_search(query, k=TOP_K, document_ids=document_ids)

    chunks = []
    for doc in results:
        chunks.append(
            {
                "filename": doc.metadata.get("filename", "unknown"),
                "page": doc.metadata.get("page", 1),
                "chunk_id": doc.metadata.get("chunk_id", ""),
                "content": doc.page_content.strip(),
            }
        )
    return chunks
    