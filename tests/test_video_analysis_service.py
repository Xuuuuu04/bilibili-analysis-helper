from unittest.mock import MagicMock, patch

import pytest

from src.backend.services.ai.video_analysis_service import VideoAnalysisService


def _make_mock_response(content_text, total_tokens=100):
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = content_text
    response.usage = MagicMock()
    response.usage.total_tokens = total_tokens
    return response


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
    return VideoAnalysisService(client=mock_client, model="test-model")


@patch("src.backend.services.ai.video_analysis_service.retry_sync")
def test_generate_full_analysis_success(mock_retry, service):
    mock_response = _make_mock_response("内容深度总结\n这是总结内容\n弹幕互动\n弹幕分析\n评论区深度\n评论分析", total_tokens=150)
    mock_retry.return_value = mock_response

    result = service.generate_full_analysis(
        video_info={"title": "Test Video"},
        content="Test content",
        video_frames=["base64frame1", "base64frame2"],
    )

    assert result["success"] is True
    assert "full_analysis" in result["data"]
    assert "parsed" in result["data"]
    assert "tokens_used" in result["data"]
    assert result["data"]["tokens_used"] == 150
    assert "内容深度总结" in result["data"]["full_analysis"]


@patch("src.backend.services.ai.video_analysis_service.retry_sync")
def test_generate_full_analysis_no_frames(mock_retry, service):
    mock_response = _make_mock_response("内容深度总结\n无帧总结", total_tokens=50)
    mock_retry.return_value = mock_response

    result = service.generate_full_analysis(
        video_info={"title": "Test Video"},
        content="Test content",
        video_frames=None,
    )

    assert result["success"] is True
    assert result["data"]["full_analysis"] == "内容深度总结\n无帧总结"


@patch("src.backend.services.ai.video_analysis_service.retry_sync")
def test_generate_full_analysis_api_error(mock_retry, service):
    mock_retry.side_effect = Exception("API connection timeout error")

    result = service.generate_full_analysis(
        video_info={"title": "Test Video"},
        content="Test content",
    )

    assert result["success"] is False
    assert "error" in result


@patch("src.backend.services.ai.video_analysis_service.retry_sync")
def test_generate_full_analysis_stream_yields_events(mock_retry, service):
    chunks = [
        _make_stream_chunk("内容深度总结\n"),
        _make_stream_chunk("这是分析内容"),
        _make_stream_chunk(""),
    ]
    mock_retry.return_value = iter(chunks)

    events = list(service.generate_full_analysis_stream(
        video_info={"title": "Test Video"},
        content="Test content",
        video_frames=None,
    ))

    event_types = [e["type"] for e in events]
    assert "start" in event_types
    assert "progress" in event_types
    assert "complete" in event_types

    complete_event = [e for e in events if e["type"] == "complete"][0]
    assert complete_event["progress"] == 100
    assert "full_analysis" in complete_event
    assert "parsed" in complete_event


@patch("src.backend.services.ai.video_analysis_service.retry_sync")
def test_generate_full_analysis_stream_fallback(mock_retry, service):
    mock_retry.side_effect = Exception("connection timeout error")

    mock_fallback_response = _make_mock_response("内容深度总结\n降级分析", total_tokens=30)
    mock_retry.side_effect = [
        Exception("connection timeout error"),
        mock_fallback_response,
    ]

    events = list(service.generate_full_analysis_stream(
        video_info={"title": "Test Video"},
        content="Test content",
        video_frames=["frame1", "frame2"],
    ))

    error_events = [e for e in events if e["type"] == "error"]
    assert len(error_events) >= 1
    assert error_events[0]["error_type"] == "network"

    fallback_events = [e for e in events if e.get("stage") == "fallback"]
    assert len(fallback_events) >= 1
