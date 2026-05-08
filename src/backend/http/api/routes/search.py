from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from src.backend.http.api.schemas import SearchRequest
from src.backend.http.dependencies import get_bilibili_service
from src.backend.services.bilibili import BilibiliService
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["search"])


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
        logger.exception("搜索失败: %s", str(e))
        return JSONResponse(status_code=500, content={"success": False, "error": "搜索失败"})
