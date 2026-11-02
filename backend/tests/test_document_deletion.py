import io
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.rag.vectorstore import get_vectorstore, delete_document

client = TestClient(app)

def test_delete_document_api_endpoint(tmp_path):
    file_content = b"This is a test document about artificial intelligence research agents."
    files = {"file": ("sample.txt", io.BytesIO(file_content), "text/plain")}

    upload_res = client.post("/api/documents/upload", files=files)
    assert upload_res.status_code == 200
    doc_id = upload_res.json()["id"]

    list_res = client.get("/api/documents")
    assert list_res.status_code == 200
    doc_ids = [d["id"] for d in list_res.json()["documents"]]
    assert doc_id in doc_ids

    del_res = client.delete(f"/api/documents/{doc_id}")
    assert del_res.status_code == 200
    assert del_res.json() == {"id": doc_id, "deleted": True}

    list_res_after = client.get("/api/documents")
    assert list_res_after.status_code == 200
    doc_ids_after = [d["id"] for d in list_res_after.json()["documents"]]
    assert doc_id not in doc_ids_after

def test_delete_nonexistent_document_returns_404():
    del_res = client.delete("/api/documents/non-existent-id-12345")
    assert del_res.status_code == 404

def test_delete_document_removes_correct_chunks():
    store = get_vectorstore()
    from langchain_core.documents import Document
    from app.rag.vectorstore import add_chunks

    doc_a = Document(page_content="Content A", metadata={"document_id": "doc-A", "chunk_id": "doc-A-0", "filename": "a.txt", "page": 1})
    doc_b = Document(page_content="Content B", metadata={"document_id": "doc-B", "chunk_id": "doc-B-0", "filename": "b.txt", "page": 1})

    add_chunks([doc_a, doc_b])

    delete_document("doc-A")

    remaining = store._collection.get(where={"document_id": "doc-A"})
    assert len(remaining["ids"]) == 0

    remaining_b = store._collection.get(where={"document_id": "doc-B"})
    assert len(remaining_b["ids"]) > 0

    delete_document("doc-B")
