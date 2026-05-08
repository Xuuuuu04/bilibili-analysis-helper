import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.backend.services.bilibili.search_service import SearchService


@pytest.fixture
def search_service():
    return SearchService(credential=MagicMock())


@pytest.mark.asyncio
async def test_search_videos_success(search_service):
    mock_search_result = {
        "result": [
            {
                "type": "video",
                "bvid": "BV1test12345",
                "title": '<em class="keyword">Test</em> Video',
                "author": "TestAuthor",
                "pic": "//pic.example.com/cover.jpg",
                "play": 1000,
                "duration": "05:30",
            },
            {
                "type": "ad",
                "bvid": "BV1ad12345",
                "title": "Ad Video",
                "author": "AdAuthor",
                "pic": "//pic.example.com/ad.jpg",
                "play": 0,
                "duration": "00:30",
            },
        ]
    }

    with patch(
        "src.backend.services.bilibili.search_service.search.search_by_type",
        new_callable=AsyncMock,
        return_value=mock_search_result,
    ) as mock_search, patch(
        "src.backend.services.bilibili.search_service.search.SearchObjectType"
    ) as MockSearchType, patch(
        "src.backend.services.bilibili.search_service.search.OrderVideo"
    ) as MockOrderVideo:
        MockSearchType.VIDEO = "video"
        MockOrderVideo.TOTALRANK = "totalrank"

        result = await search_service.search_videos("test", limit=10)

        mock_search.assert_awaited_once()
        assert result["success"] is True
        assert len(result["data"]) == 1
        assert result["data"][0]["bvid"] == "BV1test12345"
        assert result["data"][0]["title"] == "Test Video"
        assert result["data"][0]["pic"] == "https://pic.example.com/cover.jpg"


@pytest.mark.asyncio
async def test_search_videos_error(search_service):
    with patch(
        "src.backend.services.bilibili.search_service.search.search_by_type",
        new_callable=AsyncMock,
        side_effect=Exception("Search API error"),
    ), patch(
        "src.backend.services.bilibili.search_service.search.SearchObjectType"
    ) as MockSearchType, patch(
        "src.backend.services.bilibili.search_service.search.OrderVideo"
    ) as MockOrderVideo:
        MockSearchType.VIDEO = "video"
        MockOrderVideo.TOTALRANK = "totalrank"

        result = await search_service.search_videos("test")

        assert result["success"] is False
        assert "搜索视频失败" in result["error"]
        assert "Search API error" in result["error"]


@pytest.mark.asyncio
async def test_search_users_success(search_service):
    mock_search_result = {
        "result": [
            {
                "mid": 12345,
                "uname": '<em class="keyword">Test</em> User',
                "upic": "//pic.example.com/face.jpg",
                "level": 6,
                "usign": "Hello world",
            }
        ]
    }

    with patch(
        "src.backend.services.bilibili.search_service.search.search_by_type",
        new_callable=AsyncMock,
        return_value=mock_search_result,
    ) as mock_search, patch(
        "src.backend.services.bilibili.search_service.search.SearchObjectType"
    ) as MockSearchType:
        MockSearchType.USER = "user"

        result = await search_service.search_users("test", limit=5)

        mock_search.assert_awaited_once()
        assert result["success"] is True
        assert len(result["data"]) == 1
        assert result["data"][0]["mid"] == 12345
        assert result["data"][0]["name"] == "Test User"
        assert result["data"][0]["face"] == "https://pic.example.com/face.jpg"
        assert result["data"][0]["level"] == 6


@pytest.mark.asyncio
async def test_get_popular_videos_success(search_service):
    mock_hot_result = {
        "list": [
            {
                "bvid": "BV1hot12345",
                "title": "Hot Video",
                "owner": {"name": "HotAuthor"},
                "pic": "https://pic.example.com/hot.jpg",
                "duration": 300,
                "stat": {"view": 50000},
            }
        ]
    }

    hot_mock = sys.modules["bilibili_api.hot"]
    original = hot_mock.get_hot_videos
    hot_mock.get_hot_videos = AsyncMock(return_value=mock_hot_result)
    try:
        result = await search_service.get_popular_videos()

        assert result["success"] is True
        assert len(result["data"]) == 1
        assert result["data"][0]["bvid"] == "BV1hot12345"
        assert result["data"][0]["title"] == "Hot Video"
        assert result["data"][0]["author"] == "HotAuthor"
        assert result["data"][0]["view"] == 50000
    finally:
        hot_mock.get_hot_videos = original
