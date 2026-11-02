from langchain_core.documents import Document

from app.rag.splitter import split_documents


def test_split_documents_produces_chunks_with_metadata():
    long_text = "This is a sentence about research agents. " * 100
    docs = [Document(page_content=long_text, metadata={"filename": "test.txt", "page": 1})]

    chunks = split_documents(docs, document_id="doc-123")

    assert len(chunks) > 1
    for i, chunk in enumerate(chunks):
        assert chunk.metadata["document_id"] == "doc-123"
        assert chunk.metadata["chunk_id"] == f"doc-123-{i}"
        assert chunk.metadata["filename"] == "test.txt"


def test_split_documents_handles_short_text():
    docs = [Document(page_content="Short text.", metadata={"filename": "a.txt", "page": 1})]
    chunks = split_documents(docs, document_id="doc-abc")
    assert len(chunks) == 1
    assert chunks[0].page_content == "Short text."
