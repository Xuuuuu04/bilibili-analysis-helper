"""
================================================================================
B站数据路由 (src/backend/http/api/routes/bilibili.py)
================================================================================

【架构位置】
位于 HTTP 层的 API 路由子模块，定义 B站数据获取相关的 HTTP 端点。

【设计模式】
- 路由模式 (Router Pattern): 使用 FastAPI 的 APIRouter 组织路由
- 依赖注入 (Dependency Injection): 使用 Depends 注入服务实例
- 代理模式: 图片代理端点转发 B站图片资源

【主要功能】
1. 搜索服务：
   - POST /api/search - 搜索视频/专栏/用户

2. 视频数据：
   - POST /api/video/info - 获取视频信息（含统计和推荐）
   - POST /api/video/subtitle - 获取视频字幕
   - GET /api/video/popular - 获取热门视频

3. 图片代理：
   - GET /api/image-proxy - 代理 B站图片（解决跨域问题）

4. 健康检查：
   - GET /api/health - 服务健康状态

5. B站登录：
   - POST /api/bilibili/login/start - 启动扫码登录
   - POST /api/bilibili/login/status - 检查登录状态
   - POST /api/bilibili/login/logout - 登出
   - GET /api/bilibili/login/check - 检查当前登录状态

【技术要点】
- asyncio.gather(): 并行请求多个接口提升性能
- 图片代理: 添加 Referer 和 User-Agent 绕过防盗链
- 域名白名单: 仅允许 hdslb.com 和 bilibili.com

【路由前缀】
/api

================================================================================
"""

import asyncio
import urllib.parse
from typing import Optional

import aiohttp
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, Response

from src.backend.http.api.schemas import (
    LoginStatusRequest,
    SearchRequest,
    VideoInfoRequest,
    VideoSubtitleRequest,
)
from src.backend.http.dependencies import get_bilibili_service, get_login_service
from src.backend.services.bilibili import BilibiliService
from src.backend.services.bilibili.login_service import LoginService
from src.backend.utils.logger import get_logger
from src.config import Config

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["api"])


def _server_error(message: str, error: Exception) -> JSONResponse:
    logger.exception("%s: %s", message, str(error))
    return JSONResponse(status_code=500, content={"success": False, "error": message})


@router.post("/search")
async def search_content(
    payload: SearchRequest, bilibili_service: BilibiliService = Depends(get_bilibili_service)
):
    try:
        if not payload.keyword:
            return JSONResponse(
                status_code=400, content={"success": False, "error": "请输入搜索关键词"}
            )

        if payload.mode == "article":
            res = await bilibili_service.search_articles(payload.keyword, limit=10)
        elif payload.mode == "user":
            res = await bilibili_service.search_users(payload.keyword, limit=10)
        else:
            res = await bilibili_service.search_videos(payload.keyword, limit=10)
        return res
    except Exception as e:
        return _server_error("搜索失败", e)


@router.post("/video/info")
async def get_video_info(
    payload: VideoInfoRequest, bilibili_service: BilibiliService = Depends(get_bilibili_service)
):
    try:
        bvid = BilibiliService.extract_bvid(payload.url)
        if not bvid:
            return JSONResponse(
                status_code=400, content={"success": False, "error": "无效的B站视频链接"}
            )

        info_res, stats_res, related_res = await asyncio.gather(
            bilibili_service.get_video_info(bvid),
            bilibili_service.get_video_stats(bvid),
            bilibili_service.get_related_videos(bvid),
        )
        if not info_res.get("success"):
            return JSONResponse(status_code=400, content=info_res)

        video_data = info_res["data"]
        if stats_res.get("success"):
            video_data.update(stats_res["data"])

        related_videos = related_res.get("data") if related_res.get("success") else []
        return {"success": True, "data": video_data, "related": related_videos}
    except Exception as e:
        return _server_error("获取视频信息失败", e)


@router.post("/video/subtitle")
async def get_video_subtitle(
    payload: VideoSubtitleRequest, bilibili_service: BilibiliService = Depends(get_bilibili_service)
):
    try:
        bvid = BilibiliService.extract_bvid(payload.url)
        if not bvid:
            return JSONResponse(
                status_code=400, content={"success": False, "error": "无效的B站视频链接"}
            )
        return await bilibili_service.get_video_subtitles(bvid)
    except Exception as e:
        return _server_error("获取字幕失败", e)


@router.get("/video/popular")
async def get_popular_videos(bilibili_service: BilibiliService = Depends(get_bilibili_service)):
    try:
        return await bilibili_service.get_popular_videos()
    except Exception as e:
        return _server_error("获取热门视频失败", e)


@router.get("/image-proxy")
async def image_proxy(url: str = Query(min_length=1)):
    image_url = urllib.parse.unquote(url)
    if image_url.startswith("//"):
        image_url = "https:" + image_url
    elif not image_url.startswith(("http://", "https://")):
        image_url = "https://" + image_url

    parsed = urllib.parse.urlparse(image_url)
    hostname = (parsed.hostname or "").lower()
    allowed_hosts = ("hdslb.com", "bilibili.com")
    if not hostname or not any(
        hostname == domain or hostname.endswith(f".{domain}") for domain in allowed_hosts
    ):
        return JSONResponse(status_code=400, content={"error": "不支持的图片域名"})

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://www.bilibili.com",
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "identity",
            "Connection": "close",
        }

        content: Optional[bytes] = None
        content_type = "image/jpeg"
        timeout_cfg = aiohttp.ClientTimeout(total=10)

        for attempt in range(3):
            try:
                async with aiohttp.ClientSession(timeout=timeout_cfg) as session:
                    async with session.get(image_url, headers=headers) as resp:
                        if resp.status == 200:
                            content = await resp.read()
                            content_type = resp.headers.get("content-type", "image/jpeg")
                            break
                        elif attempt < 2:
                            await asyncio.sleep(0.5 * (attempt + 1))
                            continue
                        return JSONResponse(
                            status_code=404, content={"error": f"获取图片失败: {resp.status}"}
                        )
            except aiohttp.ClientError:
                if attempt < 2:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                return JSONResponse(status_code=500, content={"error": "获取图片失败"})

        if content is None:
            return JSONResponse(status_code=500, content={"error": "获取图片失败"})

        return Response(content=content, media_type=content_type)
    except Exception as e:
        logger.exception("图片代理失败: %s", str(e))
        return JSONResponse(status_code=500, content={"error": "获取图片失败"})


@router.get("/health")
def health_check():
    return {"success": True, "status": "running", "message": "BiliBili智能学习平台 Ultra版运行中"}


@router.post("/bilibili/login/start")
async def start_bilibili_login(login_service: LoginService = Depends(get_login_service)):
    try:
        return await login_service.start_login()
    except Exception as e:
        return _server_error("启动登录失败", e)


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
        return _server_error("检查登录状态失败", e)


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
        return _server_error("登出失败", e)


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
        return _server_error("检查登录状态失败", e)
