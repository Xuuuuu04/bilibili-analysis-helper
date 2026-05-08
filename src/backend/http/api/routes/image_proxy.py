import asyncio
import urllib.parse
from typing import Optional

import aiohttp
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, Response

from src.backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["image-proxy"])


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
