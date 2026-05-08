import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

for _mod_name in [
    "bilibili_api",
    "bilibili_api.article",
    "bilibili_api.dynamic",
    "bilibili_api.login_v2",
    "bilibili_api.search",
    "bilibili_api.hot",
    "bilibili_api.video",
    "bilibili_api.comment",
    "bilibili_api.user",
    "bilibili_api.rank",
    "bilibili_api.channel_series",
]:
    if _mod_name not in sys.modules:
        sys.modules[_mod_name] = MagicMock()

_bapi = sys.modules["bilibili_api"]
for _sub in [
    "article",
    "dynamic",
    "login_v2",
    "search",
    "hot",
    "video",
    "comment",
    "user",
    "rank",
    "channel_series",
]:
    setattr(_bapi, _sub, sys.modules[f"bilibili_api.{_sub}"])

from src.backend.http.app import create_app


class TestResult:
    def __init__(self, test_id: str, name: str, category: str):
        self.test_id = test_id
        self.name = name
        self.category = category
        self.passed = False
        self.error = None
        self.actual_response = None
        self.expected_response = None

    def record_pass(self, actual: Any = None):
        self.passed = True
        self.actual_response = actual

    def record_fail(self, error: str, actual: Any = None):
        self.passed = False
        self.error = error
        self.actual_response = actual

    def to_dict(self) -> dict:
        return {
            "test_id": self.test_id,
            "name": self.name,
            "category": self.category,
            "passed": self.passed,
            "error": self.error,
            "actual_response": (
                str(self.actual_response)[:200] if self.actual_response else None
            ),
        }


@pytest.fixture
def mock_openai_client():
    client = MagicMock()
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.chat.completions.create = MagicMock()
    return client


@pytest.fixture
def mock_bilibili_service():
    service = MagicMock()
    service.get_video_info = AsyncMock(
        return_value={
            "success": True,
            "data": {
                "bvid": "BV1xx411c7mD",
                "title": "Test Video",
                "desc": "Test",
                "duration": 300,
                "author": "Test Author",
                "view": 1000,
                "cover": "https://example.com/cover.jpg",
            },
        }
    )
    service.get_video_subtitles = AsyncMock(
        return_value={
            "success": True,
            "data": {
                "has_subtitle": True,
                "subtitles": [{"text": "Hello", "start_time": 0.0, "end_time": 1.0}],
            },
        }
    )
    service.get_video_danmaku = AsyncMock(
        return_value={"success": True, "data": {"danmaku": [{"text": "test", "time": 1.0}]}}
    )
    service.get_video_comments = AsyncMock(
        return_value={"success": True, "data": {"comments": [], "total": 0}}
    )
    service.get_video_stats = AsyncMock(
        return_value={
            "success": True,
            "data": {
                "view": 1000,
                "like": 100,
                "coin": 50,
                "favorite": 30,
                "share": 10,
                "danmaku": 200,
                "reply": 50,
            },
        }
    )
    service.get_related_videos = AsyncMock(return_value={"success": True, "data": []})
    service.get_popular_videos = AsyncMock(return_value={"success": True, "data": []})
    service.search_videos = AsyncMock(return_value={"success": True, "data": []})
    service.search_users = AsyncMock(return_value={"success": True, "data": []})
    service.search_articles = AsyncMock(return_value={"success": True, "data": []})
    service.get_user_info = AsyncMock(
        return_value={
            "success": True,
            "data": {"name": "Test User", "face": "https://example.com/face.jpg"},
        }
    )
    service.get_user_recent_videos = AsyncMock(return_value={"success": True, "data": []})
    service.get_article_content = AsyncMock(
        return_value={"success": True, "data": {"title": "Test Article", "content": "Test content"}}
    )
    service.get_opus_content = AsyncMock(
        return_value={"success": True, "data": {"title": "Test Opus", "content": "Test content"}}
    )
    service.check_credential_valid = AsyncMock(return_value=True)
    service.refresh_credential = MagicMock()
    service.extract_bvid = staticmethod(
        lambda url: "BV1xx411c7mD" if "BV" in url else None
    )
    return service


@pytest.fixture
def mock_credential():
    return MagicMock()


@pytest.fixture(scope="module")
def app_client():
    with TestClient(create_app()) as client:
        yield client
