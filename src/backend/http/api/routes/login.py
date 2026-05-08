from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from src.backend.http.api.schemas import LoginStatusRequest
from src.backend.http.dependencies import get_bilibili_service, get_login_service
from src.backend.services.bilibili import BilibiliService
from src.backend.services.bilibili.login_service import LoginService
from src.backend.utils.logger import get_logger
from src.config import Config

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["login"])


@router.post("/bilibili/login/start")
async def start_bilibili_login(login_service: LoginService = Depends(get_login_service)):
    try:
        return await login_service.start_login()
    except Exception as e:
        logger.exception("启动登录失败: %s", str(e))
        return JSONResponse(status_code=500, content={"success": False, "error": "启动登录失败"})


@router.post("/bilibili/login/status")
async def check_login_status(
    payload: LoginStatusRequest,
    bilibili_service: BilibiliService = Depends(get_bilibili_service),
    login_service: LoginService = Depends(get_login_service),
):
    try:
        if not payload.session_id:
            return JSONResponse(
                status_code=400, content={"success": False, "error": "缺少session_id"}
            )

        result = await login_service.check_login_status(payload.session_id)
        if result.get("success") and result.get("data", {}).get("status") == "success":
            bilibili_service.refresh_credential()
        return result
    except Exception as e:
        logger.exception("检查登录状态失败: %s", str(e))
        return JSONResponse(status_code=500, content={"success": False, "error": "检查登录状态失败"})


@router.post("/bilibili/login/logout")
async def logout_bilibili(
    bilibili_service: BilibiliService = Depends(get_bilibili_service),
    login_service: LoginService = Depends(get_login_service),
):
    try:
        result = await login_service.logout()
        bilibili_service.refresh_credential()
        return result
    except Exception as e:
        logger.exception("登出失败: %s", str(e))
        return JSONResponse(status_code=500, content={"success": False, "error": "登出失败"})


@router.get("/bilibili/login/check")
async def check_current_login(bilibili_service: BilibiliService = Depends(get_bilibili_service)):
    try:
        has_credentials = all(
            [Config.BILIBILI_SESSDATA, Config.BILIBILI_BILI_JCT, Config.BILIBILI_DEDEUSERID]
        )
        if has_credentials:
            is_valid = await bilibili_service.check_credential_valid()
            if is_valid:
                user_info_res = await bilibili_service.get_user_info(
                    int(Config.BILIBILI_DEDEUSERID)
                )
                if user_info_res.get("success"):
                    return {
                        "success": True,
                        "data": {
                            "is_logged_in": True,
                            "user_id": Config.BILIBILI_DEDEUSERID,
                            "name": user_info_res["data"]["name"],
                            "face": user_info_res["data"]["face"],
                            "message": "已登录",
                        },
                    }
            return {
                "success": True,
                "data": {
                    "is_logged_in": is_valid,
                    "user_id": (
                        (Config.BILIBILI_DEDEUSERID[:10] + "***")
                        if Config.BILIBILI_DEDEUSERID
                        else None
                    ),
                    "message": "凭据已失效，请重新登录" if not is_valid else "获取用户信息失败",
                },
            }

        return {
            "success": True,
            "data": {"is_logged_in": False, "user_id": None, "message": "未登录"},
        }
    except Exception as e:
        logger.exception("检查登录状态失败: %s", str(e))
        return JSONResponse(status_code=500, content={"success": False, "error": "检查登录状态失败"})
