from unittest.mock import MagicMock, patch

from src.backend.services.ai.web_search import web_search_exa
from src.backend.services.ai.cache import EXA_CACHE


def test_no_api_key():
    with patch("src.backend.services.ai.web_search.Config") as mock_config:
        mock_config.EXA_API_KEY = None
        result = web_search_exa("test query")

    assert result["success"] is False
    assert "error" in result


@patch("src.backend.services.ai.web_search._sleep_backoff")
@patch("src.backend.services.ai.web_search._semaphore")
@patch("src.backend.services.ai.web_search.requests.post")
@patch("src.backend.services.ai.web_search.Config")
def test_successful_search(mock_config, mock_post, mock_semaphore, mock_sleep):
    mock_config.EXA_API_KEY = "test-api-key"
    mock_semaphore.return_value.__enter__ = MagicMock(return_value=None)
    mock_semaphore.return_value.__exit__ = MagicMock(return_value=False)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {"title": "Result 1", "url": "https://example.com/1", "publishedDate": "2024-01-01"},
            {"title": "Result 2", "url": "https://example.com/2", "publishedDate": "2024-01-02"},
        ]
    }
    mock_post.return_value = mock_response

    EXA_CACHE._store.clear()

    result = web_search_exa("test query")

    assert result["success"] is True
    assert len(result["data"]) == 2
    assert result["data"][0]["title"] == "Result 1"
    assert result["data"][0]["url"] == "https://example.com/1"
    assert result["data"][1]["title"] == "Result 2"


@patch("src.backend.services.ai.web_search._sleep_backoff")
@patch("src.backend.services.ai.web_search._semaphore")
@patch("src.backend.services.ai.web_search.requests.post")
@patch("src.backend.services.ai.web_search.Config")
def test_cached_result(mock_config, mock_post, mock_semaphore, mock_sleep):
    mock_config.EXA_API_KEY = "test-api-key"
    mock_semaphore.return_value.__enter__ = MagicMock(return_value=None)
    mock_semaphore.return_value.__exit__ = MagicMock(return_value=False)

    cached_data = [{"title": "Cached", "url": "https://cached.com", "published_date": "2024-01-01"}]
    EXA_CACHE.set(("exa_search", "cached query"), cached_data, ttl_seconds=600)

    result = web_search_exa("cached query")

    assert result["success"] is True
    assert result["data"] == cached_data
    mock_post.assert_not_called()

    EXA_CACHE._store.clear()


@patch("src.backend.services.ai.web_search._sleep_backoff")
@patch("src.backend.services.ai.web_search._semaphore")
@patch("src.backend.services.ai.web_search.requests.post")
@patch("src.backend.services.ai.web_search.Config")
def test_http_error(mock_config, mock_post, mock_semaphore, mock_sleep):
    mock_config.EXA_API_KEY = "test-api-key"
    mock_semaphore.return_value.__enter__ = MagicMock(return_value=None)
    mock_semaphore.return_value.__exit__ = MagicMock(return_value=False)

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.json.return_value = {"error": "Internal Server Error"}
    mock_post.return_value = mock_response

    EXA_CACHE._store.clear()

    result = web_search_exa("test query")

    assert result["success"] is False
    assert "error" in result
