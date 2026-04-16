from fastapi.testclient import TestClient

from src.backend.http.app import create_app


def test_request_id_header_is_attached() -> None:
    client = TestClient(create_app())
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID")


def test_request_id_header_passthrough() -> None:
    client = TestClient(create_app())
    response = client.get("/api/health", headers={"X-Request-ID": "req-test-1"})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == "req-test-1"
