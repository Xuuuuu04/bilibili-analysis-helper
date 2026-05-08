from unittest.mock import MagicMock, patch

import pytest

from src.backend.services.ai.chat_service import ChatService


def _make_stream_chunk(content):
    chunk = MagicMock()
    delta = MagicMock()
    delta.content = content
    chunk.choices = [MagicMock()]
    chunk.choices[0].delta = delta
    return chunk


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.chat.completions.create = MagicMock()
    return client


@pytest.fixture
def service(mock_client):
    return ChatService(client=mock_client, qa_model="test-qa-model")


@patch("src.backend.services.ai.chat_service.retry_sync")
def test_chat_stream_yields_content(mock_retry, service):
    chunks = [
        _make_stream_chunk("Hello "),
        _make_stream_chunk("world"),
    ]
    mock_retry.return_value = iter(chunks)

    events = list(service.chat_stream(
        question="Hi",
        context="video context",
        video_info={"title": "Test"},
    ))

    content_events = [e for e in events if e["type"] == "content"]
    assert len(content_events) == 2
    assert content_events[0]["content"] == "Hello "
    assert content_events[1]["content"] == "world"


@patch("src.backend.services.ai.chat_service.retry_sync")
def test_chat_stream_yields_done(mock_retry, service):
    chunks = [_make_stream_chunk("response")]
    mock_retry.return_value = iter(chunks)

    events = list(service.chat_stream(
        question="Hi",
        context="context",
        video_info={},
    ))

    done_events = [e for e in events if e["type"] == "done"]
    assert len(done_events) == 1


@patch("src.backend.services.ai.chat_service.retry_sync")
def test_chat_stream_with_history(mock_retry, service):
    chunks = [_make_stream_chunk("answer")]
    mock_retry.return_value = iter(chunks)

    history = [
        {"role": "user", "content": "previous question"},
        {"role": "assistant", "content": "previous answer"},
    ]

    events = list(service.chat_stream(
        question="follow up",
        context="context",
        video_info={},
        history=history,
    ))

    fn = mock_retry.call_args[0][0]
    fn()
    call_kwargs = service.client.chat.completions.create.call_args[1]
    messages = call_kwargs["messages"]
    assert len(messages) == 4
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "previous question"
    assert messages[2]["role"] == "assistant"
    assert messages[2]["content"] == "previous answer"
    assert messages[3]["role"] == "user"
    assert messages[3]["content"] == "follow up"

    content_events = [e for e in events if e["type"] == "content"]
    assert len(content_events) == 1


@patch("src.backend.services.ai.chat_service.retry_sync")
def test_chat_stream_error(mock_retry, service):
    mock_retry.side_effect = Exception("API error")

    events = list(service.chat_stream(
        question="Hi",
        context="context",
        video_info={},
    ))

    error_events = [e for e in events if e["type"] == "error"]
    assert len(error_events) == 1
    assert "API error" in error_events[0]["error"]


@patch("src.backend.services.ai.chat_service.retry_sync")
def test_context_qa_stream_yields_content(mock_retry, service):
    chunks = [
        _make_stream_chunk("Context "),
        _make_stream_chunk("answer"),
    ]
    mock_retry.return_value = iter(chunks)

    events = list(service.context_qa_stream(
        mode="video",
        question="What is this?",
        context="some context",
        meta={"title": "Test"},
    ))

    content_events = [e for e in events if e["type"] == "content"]
    assert len(content_events) == 2
    assert content_events[0]["content"] == "Context "
    assert content_events[1]["content"] == "answer"

    done_events = [e for e in events if e["type"] == "done"]
    assert len(done_events) == 1
