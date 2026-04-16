import pytest

from src.backend.services.bilibili.video_service import VideoService


class _FakeResponse:
    def __init__(self, status: int, payload: dict | None = None, content: bytes = b""):
        self.status = status
        self._payload = payload or {}
        self._content = content

    async def json(self):
        return self._payload

    async def read(self):
        return self._content


class _FakeRequestCtx:
    def __init__(self, response: _FakeResponse):
        self._response = response

    async def __aenter__(self):
        return self._response

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeClientSession:
    def __init__(self, *args, **kwargs):
        del args, kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def get(self, url, headers=None):
        del headers
        if "videoshot" in url:
            return _FakeRequestCtx(_FakeResponse(status=200, payload={"code": -1}))
        return _FakeRequestCtx(_FakeResponse(status=404))


@pytest.mark.asyncio
async def test_extract_frames_fallback_does_not_raise_name_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "src.backend.services.bilibili.video_service.aiohttp.ClientSession", _FakeClientSession
    )

    service = VideoService()

    async def _fake_get_cid(_bvid: str):
        return 123

    async def _fake_get_info(_bvid: str):
        return {
            "success": True,
            "data": {"duration": 120, "cover": "https://example.com/cover.jpg"},
        }

    monkeypatch.setattr(service, "get_cid", _fake_get_cid)
    monkeypatch.setattr(service, "get_info", _fake_get_info)

    result = await service.extract_frames("BV1xx411c7mD")
    assert result["success"] is False
    assert "封面回退失败" in result["error"]
