from fastapi.testclient import TestClient

from src.backend.http.app import create_app


def test_settings_do_not_leak_secrets() -> None:
    client = TestClient(create_app())
    resp = client.get("/api/settings")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload.get("success") is True
    data = payload.get("data") or {}
    assert "openai_api_key" not in data
    assert "exa_api_key" not in data
    assert "openai_api_key_set" in data
    assert "exa_api_key_set" in data
