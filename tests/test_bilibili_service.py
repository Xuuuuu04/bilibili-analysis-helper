from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.backend.services.bilibili.bilibili_service import BilibiliService


@pytest.fixture
def bilibili_service():
    with patch(
        "src.backend.services.bilibili.bilibili_service.CredentialManager"
    ) as MockCredMgr:
        mock_cred_mgr = MockCredMgr.return_value
        mock_cred_mgr.credential = MagicMock()
        mock_cred_mgr.refresh = MagicMock()

        with patch(
            "src.backend.services.bilibili.bilibili_service.VideoService"
        ) as MockVideo:
            with patch(
                "src.backend.services.bilibili.bilibili_service.UserService"
            ) as MockUser:
                with patch(
                    "src.backend.services.bilibili.bilibili_service.SearchService"
                ) as MockSearch:
                    with patch(
                        "src.backend.services.bilibili.bilibili_service.ContentService"
                    ) as MockContent:
                        mock_video = MockVideo.return_value
                        mock_user = MockUser.return_value
                        mock_search = MockSearch.return_value
                        mock_content = MockContent.return_value

                        mock_video.get_info = AsyncMock(
                            return_value={"success": True, "data": {"bvid": "BV1test"}}
                        )
                        mock_video.get_subtitles = AsyncMock(
                            return_value={"success": True, "data": []}
                        )
                        mock_search.search_videos = AsyncMock(
                            return_value={"success": True, "data": []}
                        )
                        mock_user.get_info = AsyncMock(
                            return_value={"success": True, "data": {"name": "test"}}
                        )
                        mock_content.get_article_content = AsyncMock(
                            return_value={"success": True, "data": {"title": "article"}}
                        )

                        service = BilibiliService()

                        service.video = mock_video
                        service.user = mock_user
                        service.search = mock_search
                        service.content = mock_content
                        service._credential_manager = mock_cred_mgr

    return service


@pytest.mark.asyncio
async def test_delegates_get_video_info(bilibili_service):
    result = await bilibili_service.get_video_info("BV1test")
    bilibili_service.video.get_info.assert_awaited_once_with("BV1test")
    assert result == {"success": True, "data": {"bvid": "BV1test"}}


@pytest.mark.asyncio
async def test_delegates_get_video_subtitles(bilibili_service):
    result = await bilibili_service.get_video_subtitles("BV1test")
    bilibili_service.video.get_subtitles.assert_awaited_once_with("BV1test")
    assert result == {"success": True, "data": []}


@pytest.mark.asyncio
async def test_delegates_search_videos(bilibili_service):
    result = await bilibili_service.search_videos("test keyword", limit=10)
    bilibili_service.search.search_videos.assert_awaited_once_with("test keyword", 10)
    assert result == {"success": True, "data": []}


@pytest.mark.asyncio
async def test_delegates_get_user_info(bilibili_service):
    result = await bilibili_service.get_user_info(12345)
    bilibili_service.user.get_info.assert_awaited_once_with(12345)
    assert result == {"success": True, "data": {"name": "test"}}


@pytest.mark.asyncio
async def test_delegates_get_article_content(bilibili_service):
    result = await bilibili_service.get_article_content(999)
    bilibili_service.content.get_article_content.assert_awaited_once_with(999)
    assert result == {"success": True, "data": {"title": "article"}}


def test_refresh_credential(bilibili_service):
    new_cred = MagicMock()
    bilibili_service._credential_manager.credential = new_cred

    bilibili_service.refresh_credential()

    bilibili_service._credential_manager.refresh.assert_called_once()
    assert bilibili_service.video.credential is new_cred
    assert bilibili_service.user.credential is new_cred
    assert bilibili_service.search.credential is new_cred
    assert bilibili_service.content.credential is new_cred


def test_extract_bvid_static():
    assert BilibiliService.extract_bvid("https://www.bilibili.com/video/BV1xx411c7mD") == "BV1xx411c7mD"
    assert BilibiliService.extract_bvid("BV1xx411c7mD") == "BV1xx411c7mD"
    assert BilibiliService.extract_bvid("https://example.com/no-bvid") is None
