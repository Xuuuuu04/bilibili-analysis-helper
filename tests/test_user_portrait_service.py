from unittest.mock import MagicMock, patch

import pytest

from src.backend.services.ai.user_portrait_service import UserPortraitService


def _make_mock_response(content_text, total_tokens=100):
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = content_text
    response.usage = MagicMock()
    response.usage.total_tokens = total_tokens
    return response


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.chat.completions.create = MagicMock()
    return client


@pytest.fixture
def service(mock_client):
    return UserPortraitService(client=mock_client, model="test-model", qa_model="test-qa-model")


@patch("src.backend.services.ai.user_portrait_service.retry_sync")
def test_generate_summary_success(mock_retry, service):
    mock_response = _make_mock_response("This is a summary of the video.", total_tokens=80)
    mock_retry.return_value = mock_response

    result = service.generate_summary(
        video_info={"title": "Test Video"},
        content="Video content here",
    )

    assert result["success"] is True
    assert result["data"]["summary"] == "This is a summary of the video."
    assert result["data"]["tokens_used"] == 80


@patch("src.backend.services.ai.user_portrait_service.retry_sync")
def test_generate_summary_error(mock_retry, service):
    mock_retry.side_effect = Exception("API timeout error")

    result = service.generate_summary(
        video_info={"title": "Test Video"},
        content="Video content here",
    )

    assert result["success"] is False
    assert "error" in result
    assert "API timeout error" in result["error"]


@patch("src.backend.services.ai.user_portrait_service.retry_sync")
def test_generate_mindmap_success(mock_retry, service):
    mock_response = _make_mock_response("# Mind Map\n- Node 1\n  - Sub 1\n- Node 2", total_tokens=60)
    mock_retry.return_value = mock_response

    result = service.generate_mindmap(
        video_info={"title": "Test Video"},
        content="Video content here",
        summary="A summary",
    )

    assert result["success"] is True
    assert result["data"]["mindmap"] == "# Mind Map\n- Node 1\n  - Sub 1\n- Node 2"
    assert result["data"]["tokens_used"] == 60


@patch("src.backend.services.ai.user_portrait_service.retry_sync")
def test_generate_user_analysis_success(mock_retry, service):
    mock_response = _make_mock_response("This UP主 focuses on tech content.", total_tokens=120)
    mock_retry.return_value = mock_response

    user_info = {"name": "TechUP", "mid": 12345}
    recent_videos = [
        {"title": "Python Tutorial", "play": 10000, "length": "10:30"},
        {"title": "AI News", "play": 5000, "length": "8:00"},
    ]

    result = service.generate_user_analysis(user_info=user_info, recent_videos=recent_videos)

    assert "portrait" in result
    assert result["portrait"] == "This UP主 focuses on tech content."
    assert result["tokens_used"] == 120
