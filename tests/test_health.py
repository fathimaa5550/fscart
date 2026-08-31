"""
Tests for the /health endpoints.
Uses FastAPI's TestClient (sync) backed by an in-memory SQLite database.
"""
from fastapi.testclient import TestClient


class TestHealthLiveness:
    def test_health_returns_200(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_fields(self, client: TestClient) -> None:
        body = client.get("/health").json()
        assert body["status"] == "ok"
        assert "app" in body
        assert "version" in body
        assert "environment" in body

    def test_health_app_name(self, client: TestClient) -> None:
        body = client.get("/health").json()
        assert body["app"] == "fscart"


class TestHealthReadiness:
    def test_ready_returns_200(self, client: TestClient) -> None:
        response = client.get("/health/ready")
        assert response.status_code == 200

    def test_ready_response_fields(self, client: TestClient) -> None:
        body = client.get("/health/ready").json()
        assert body["status"] == "ready"
        assert body["database"] == "connected"
        assert "app" in body
        assert "version" in body
        assert "environment" in body
