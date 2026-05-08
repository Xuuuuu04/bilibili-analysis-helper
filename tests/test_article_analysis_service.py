from unittest.mock import MagicMock, patch

import pytest

from src.backend.services.ai.article_analysis_service import ArticleAnalysisService


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
    return ArticleAnalysisService(client=mock_client, qa_model="test-qa-model")


@patch("src.backend.services.ai.article_analysis_service.retry_sync")
def test_generate_article_analysis_stream_yields_content(mock_retry, service):
    chunks = [
        _make_stream_chunk("Article "),
        _make_stream_chunk("analysis content"),
    ]
    mock_retry.return_value = iter(chunks)

    events = list(service.generate_article_analysis_stream(
        article_info={"title": "Test Article"},
        content="Article body text",
    ))

    content_events = [e for e in events if e["type"] == "content"]
    assert len(content_events) == 2
    assert content_events[0]["content"] == "Article "
    assert content_events[1]["content"] == "analysis content"

    final_events = [e for e in events if e["type"] == "final"]
    assert len(final_events) == 1
    assert "parsed" in final_events[0]
    assert "full_analysis" in final_events[0]
    assert final_events[0]["full_analysis"] == "Article analysis content"
    assert final_events[0]["parsed"]["summary"] == "Article analysis content"
    assert final_events[0]["parsed"]["danmaku"] == "专栏文章暂无弹幕分析"
    assert final_events[0]["parsed"]["comments"] == "专栏文章暂无评论分析"


@patch("src.backend.services.ai.article_analysis_service.retry_sync")
def test_generate_article_analysis_stream_error(mock_retry, service):
    mock_retry.side_effect = Exception("API error occurred")

    events = list(service.generate_article_analysis_stream(
        article_info={"title": "Test Article"},
        content="Article body text",
    ))

    error_events = [e for e in events if e["type"] == "error"]
    assert len(error_events) == 1
    assert "API error occurred" in error_events[0]["error"]
