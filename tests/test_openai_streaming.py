from unittest.mock import MagicMock, patch

import pytest

from src.backend.services.ai.openai_streaming import openai_chat_completions_stream


def _make_chunk(content):
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


@patch("src.backend.services.ai.openai_streaming._sleep_backoff")
@patch("src.backend.services.ai.openai_streaming._semaphore")
def test_successful_stream(mock_semaphore, mock_sleep, mock_client):
    chunks = [_make_chunk("Hello "), _make_chunk("world")]
    mock_client.chat.completions.create.return_value = iter(chunks)
    mock_semaphore.return_value.__enter__ = MagicMock(return_value=None)
    mock_semaphore.return_value.__exit__ = MagicMock(return_value=False)

    results = list(openai_chat_completions_stream(mock_client, model="test-model", messages=[]))

    assert len(results) == 2
    assert results[0].choices[0].delta.content == "Hello "
    assert results[1].choices[0].delta.content == "world"


@patch("src.backend.services.ai.openai_streaming._sleep_backoff")
@patch("src.backend.services.ai.openai_streaming._semaphore")
def test_retry_on_429(mock_semaphore, mock_sleep, mock_client):
    error_429 = Exception("429 Rate limit exceeded")
    chunks = [_make_chunk("Success")]
    mock_client.chat.completions.create.side_effect = [error_429, iter(chunks)]
    mock_semaphore.return_value.__enter__ = MagicMock(return_value=None)
    mock_semaphore.return_value.__exit__ = MagicMock(return_value=False)

    results = list(openai_chat_completions_stream(mock_client, max_retries=4, model="test-model", messages=[]))

    assert len(results) == 1
    assert results[0].choices[0].delta.content == "Success"
    mock_sleep.assert_called_once()


@patch("src.backend.services.ai.openai_streaming._sleep_backoff")
@patch("src.backend.services.ai.openai_streaming._semaphore")
def test_no_retry_on_non_retryable(mock_semaphore, mock_sleep, mock_client):
    mock_client.chat.completions.create.side_effect = ValueError("Invalid request")
    mock_semaphore.return_value.__enter__ = MagicMock(return_value=None)
    mock_semaphore.return_value.__exit__ = MagicMock(return_value=False)

    with pytest.raises(ValueError, match="Invalid request"):
        list(openai_chat_completions_stream(mock_client, max_retries=4, model="test-model", messages=[]))

    mock_sleep.assert_not_called()


@patch("src.backend.services.ai.openai_streaming._sleep_backoff")
@patch("src.backend.services.ai.openai_streaming._semaphore")
def test_max_retries_exceeded(mock_semaphore, mock_sleep, mock_client):
    error_429 = Exception("429 Rate limit exceeded")
    mock_client.chat.completions.create.side_effect = error_429
    mock_semaphore.return_value.__enter__ = MagicMock(return_value=None)
    mock_semaphore.return_value.__exit__ = MagicMock(return_value=False)

    with pytest.raises(Exception, match="429 Rate limit exceeded"):
        list(openai_chat_completions_stream(mock_client, max_retries=2, model="test-model", messages=[]))

    assert mock_sleep.call_count == 2
