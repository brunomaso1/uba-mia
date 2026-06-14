from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_test_endpoint_returns_backend_info():
    response = client.get("/test")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "Expense API"
    assert body["api_prefix"] == "/api/v1"
    assert "version" in body
    assert body["version"]
