from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.backend.services.bilibili.login_service import LoginService


@pytest.fixture
def login_service():
    return LoginService()


@pytest.mark.asyncio
async def test_start_login_success(login_service):
    mock_qr_login = MagicMock()
    mock_qr_login.generate_qrcode = AsyncMock(return_value=None)

    mock_picture = MagicMock()
    mock_picture.content = b"\x89PNG\r\n\x1a\nfake_png_data"
    mock_qr_login.get_qrcode_picture.return_value = mock_picture

    with patch(
        "src.backend.services.bilibili.login_service.login_v2.QrCodeLogin",
        return_value=mock_qr_login,
    ) as MockQrCodeLogin, patch(
        "src.backend.services.bilibili.login_service.login_v2.QrCodeLoginChannel"
    ) as MockChannel:
        MockChannel.WEB = "web"

        result = await login_service.start_login()

        MockQrCodeLogin.assert_called_once_with(platform="web")
        mock_qr_login.generate_qrcode.assert_awaited_once()
        assert result["success"] is True
        assert "session_id" in result["data"]
        assert "qr_code" in result["data"]
        assert result["data"]["qr_code"].startswith("data:image/png;base64,")
        assert "message" in result["data"]


@pytest.mark.asyncio
async def test_start_login_error(login_service):
    with patch(
        "src.backend.services.bilibili.login_service.login_v2.QrCodeLogin",
        side_effect=Exception("QR generation failed"),
    ), patch(
        "src.backend.services.bilibili.login_service.login_v2.QrCodeLoginChannel"
    ) as MockChannel:
        MockChannel.WEB = "web"

        result = await login_service.start_login()

        assert result["success"] is False
        assert "生成QR码失败" in result["error"]
        assert "QR generation failed" in result["error"]


@pytest.mark.asyncio
async def test_check_login_status_success(login_service):
    mock_qr_login = MagicMock()
    mock_credential = MagicMock()
    mock_credential.get_cookies.return_value = {
        "SESSDATA": "test_sess",
        "bili_jct": "test_jct",
        "buvid3": "test_buvid3",
        "DedeUserID": "test_uid",
    }

    mock_qr_login.check_state = AsyncMock(return_value="DONE")
    mock_qr_login.get_credential.return_value = mock_credential

    with patch(
        "src.backend.services.bilibili.login_service.login_v2.QrCodeLoginEvents"
    ) as MockEvents:
        MockEvents.DONE = "DONE"
        MockEvents.TIMEOUT = "TIMEOUT"
        MockEvents.SCAN = "SCAN"
        MockEvents.CONF = "CONF"

        session_id = "qr_1234567890"
        login_service.active_sessions[session_id] = {
            "qr_login": mock_qr_login,
            "created_at": 1234567890.0,
        }

        with patch.object(
            login_service, "_save_credentials", new_callable=AsyncMock, return_value=True
        ):
            result = await login_service.check_login_status(session_id)

            assert result["success"] is True
            assert result["data"]["status"] == "success"
            assert session_id not in login_service.active_sessions


@pytest.mark.asyncio
async def test_logout_success(login_service):
    login_service.active_sessions = {"session1": MagicMock(), "session2": MagicMock()}

    with patch(
        "src.backend.services.bilibili.login_service.rewrite_env_with_filter"
    ) as mock_rewrite:
        result = await login_service.logout()

        mock_rewrite.assert_called_once()
        assert result["success"] is True
        assert result["data"]["message"] == "已成功登出，凭据已清理"
        assert len(login_service.active_sessions) == 0
