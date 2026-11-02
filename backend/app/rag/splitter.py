"""
Chunking.

We use LangChain's RecursiveCharacterTextSplitter, which tries to
split on paragraph breaks first, then sentences, then words — only
falling back to a hard character cut as a last resort. This keeps
each chunk semantically coherent, which matters a lot for retrieval
quality.

Each resulting chunk keeps the `filename` and `page` metadata from
its parent Document, plus a fresh `chunk_id` so we can trace any
retrieved chunk back to an exact location for citations.
"""

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def split_documents(documents: list[Document], document_id: str) -> list[Document]:
    """Split page-level Documents into retrieval-sized chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_documents(documents)

    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = f"{document_id}-{i}"
        chunk.metadata["document_id"] = document_id

    return chunks
