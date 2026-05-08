import asyncio

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from src.backend.http.api.schemas import VideoInfoRequest, VideoSubtitleRequest
from src.backend.http.dependencies import get_bilibili_service
from src.backend.services.bilibili import BilibiliService
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["video"])


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
        logger.exception("获取视频信息失败: %s", str(e))
        return JSONResponse(status_code=500, content={"success": False, "error": "获取视频信息失败"})


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
        logger.exception("获取字幕失败: %s", str(e))
        return JSONResponse(status_code=500, content={"success": False, "error": "获取字幕失败"})


@router.get("/video/popular")
async def get_popular_videos(bilibili_service: BilibiliService = Depends(get_bilibili_service)):
    try:
        return await bilibili_service.get_popular_videos()
    except Exception as e:
        logger.exception("获取热门视频失败: %s", str(e))
        return JSONResponse(status_code=500, content={"success": False, "error": "获取热门视频失败"})
