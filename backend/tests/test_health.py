from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "groq_configured" in body
    assert "tavily_configured" in body


def test_research_rejects_empty_question():
    response = client.post("/api/research", json={"question": "   ", "mode": "auto"})
    assert response.status_code == 400


def test_documents_list_returns_array():
    response = client.get("/api/documents")
    assert response.status_code == 200
    assert isinstance(response.json()["documents"], list)
