from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.backend.services.data_sources.adapter import DataSourceAdapter
from src.backend.services.data_sources.exceptions import UnsupportedPlatformError
from src.backend.services.data_sources.factory import DataSourceFactory


@pytest.mark.asyncio
async def test_adapter_resolves_bilibili_url():
    mock_source = MagicMock()
    mock_source.platform_name = "bilibili"
    mock_source.extract_video_id = AsyncMock(return_value="BV1xx411c7mD")
    mock_source.get_video_info = AsyncMock(
        return_value={"success": True, "data": {"title": "test"}, "platform": "bilibili"}
    )

    with patch.object(DataSourceFactory, "get_platform_from_url", return_value="bilibili"):
        with patch.object(DataSourceFactory, "create_from_url", return_value=mock_source):
            adapter = DataSourceAdapter()
            result = await adapter.get_video_info("https://www.bilibili.com/video/BV1xx411c7mD")

    mock_source.extract_video_id.assert_awaited_once_with("https://www.bilibili.com/video/BV1xx411c7mD")
    mock_source.get_video_info.assert_awaited_once_with("BV1xx411c7mD")
    assert result["success"] is True


@pytest.mark.asyncio
async def test_adapter_resolves_youtube_url():
    mock_source = MagicMock()
    mock_source.platform_name = "youtube"
    mock_source.extract_video_id = AsyncMock(return_value="dQw4w9WgXcQ")
    mock_source.get_video_info = AsyncMock(
        return_value={"success": True, "data": {"title": "yt_video"}, "platform": "youtube"}
    )

    with patch.object(DataSourceFactory, "get_platform_from_url", return_value="youtube"):
        with patch.object(DataSourceFactory, "create_from_url", return_value=mock_source):
            adapter = DataSourceAdapter()
            result = await adapter.get_video_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    mock_source.extract_video_id.assert_awaited_once_with("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    mock_source.get_video_info.assert_awaited_once_with("dQw4w9WgXcQ")
    assert result["success"] is True


@pytest.mark.asyncio
async def test_adapter_unsupported_url():
    with patch.object(
        DataSourceFactory,
        "get_platform_from_url",
        return_value=None,
    ):
        with patch.object(
            DataSourceFactory,
            "create_from_url",
            side_effect=UnsupportedPlatformError("https://unknown.site/video/123"),
        ):
            adapter = DataSourceAdapter()
            result = await adapter.get_video_info("https://unknown.site/video/123")

    assert result["success"] is False
    assert result["platform"] is None


def test_factory_creates_bilibili_source():
    mock_instance = MagicMock()
    mock_instance.platform_name = "bilibili"
    mock_cls = MagicMock(return_value=mock_instance)
    mock_cls.__name__ = "MockBilibiliSource"

    with patch.dict(
        DataSourceFactory._registered_sources,
        {"bilibili.com": mock_cls},
        clear=True,
    ):
        DataSourceFactory._instance_cache.clear()
        source = DataSourceFactory.create_by_platform("bilibili", use_cache=False)
        mock_cls.assert_called_once()
        assert source.platform_name == "bilibili"


def test_factory_unsupported_platform():
    with patch.dict(DataSourceFactory._registered_sources, {}, clear=True):
        DataSourceFactory._instance_cache.clear()
        with pytest.raises(UnsupportedPlatformError):
            DataSourceFactory.create_by_platform("nonexistent_platform", use_cache=False)
