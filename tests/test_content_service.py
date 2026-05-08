from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.backend.services.bilibili.content_service import ContentService


@pytest.fixture
def content_service():
    return ContentService(credential=MagicMock())


@pytest.mark.asyncio
async def test_get_article_content_success(content_service):
    mock_art_instance = MagicMock()
    mock_art_instance.get_info = AsyncMock(
        return_value={
            "title": "Test Article",
            "author_name": "Test Author",
            "stats": {"view": 100, "like": 50},
            "banner_url": "https://example.com/banner.jpg",
        }
    )
    mock_art_instance.fetch_content = AsyncMock(return_value=None)

    node1 = MagicMock()
    node1.markdown.return_value = "Hello world"
    node2 = MagicMock()
    node2.markdown.return_value = "Second paragraph"
    mock_art_instance._Article__children = [node1, node2]

    with patch(
        "src.backend.services.bilibili.content_service.article.Article",
        return_value=mock_art_instance,
    ) as MockArticle:
        result = await content_service.get_article_content(12345)

        MockArticle.assert_called_once_with(12345, credential=content_service.credential)
        assert result["success"] is True
        assert result["data"]["title"] == "Test Article"
        assert result["data"]["author"] == "Test Author"
        assert result["data"]["view"] == 100
        assert result["data"]["like"] == 50
        assert "Hello world" in result["data"]["content"]
        assert "Second paragraph" in result["data"]["content"]


@pytest.mark.asyncio
async def test_get_article_content_error(content_service):
    with patch(
        "src.backend.services.bilibili.content_service.article.Article",
        side_effect=Exception("API error"),
    ):
        result = await content_service.get_article_content(99999)

        assert result["success"] is False
        assert "获取专栏失败" in result["error"]
        assert "API error" in result["error"]


@pytest.mark.asyncio
async def test_get_opus_content_success(content_service):
    mock_dyn_instance = MagicMock()
    mock_dyn_instance.get_info = AsyncMock(
        return_value={
            "item": {
                "modules": {
                    "module_author": {"name": "Opus Author", "face": "https://face.jpg"},
                    "module_dynamic": {
                        "major": {
                            "opus": {
                                "title": "Opus Title",
                                "summary": {"text": "Opus content text"},
                                "jump_url": "",
                            }
                        }
                    },
                    "module_stat": {
                        "view": {"count": 200},
                        "like": {"count": 80},
                    },
                }
            }
        }
    )

    with patch(
        "src.backend.services.bilibili.content_service.dynamic.Dynamic",
        return_value=mock_dyn_instance,
    ) as MockDynamic:
        result = await content_service.get_opus_content(67890)

        MockDynamic.assert_called_once_with(67890, credential=content_service.credential)
        assert result["success"] is True
        assert result["data"]["title"] == "Opus Title"
        assert result["data"]["author"] == "Opus Author"
        assert result["data"]["content"] == "Opus content text"
        assert result["data"]["view"] == 200
        assert result["data"]["like"] == 80


@pytest.mark.asyncio
async def test_get_opus_content_error(content_service):
    with patch(
        "src.backend.services.bilibili.content_service.dynamic.Dynamic",
        side_effect=Exception("Dynamic API error"),
    ):
        result = await content_service.get_opus_content(11111)

        assert result["success"] is False
        assert "获取Opus内容失败" in result["error"]
        assert "Dynamic API error" in result["error"]
