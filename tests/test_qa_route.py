from fastapi.testclient import TestClient

from src.backend.http.app import create_app


def test_qa_stream_requires_question_and_context() -> None:
    client = TestClient(create_app())
    resp = client.post("/api/qa/stream", json={"question": "", "context": ""})
    assert resp.status_code == 400
