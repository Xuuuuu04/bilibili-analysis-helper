"""
获取B站热门视频工具
"""

from typing import Dict

from src.backend.services.ai.toolkit.base_tool import BaseTool
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class GetHotVideosTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_hot_videos"

    @property
    def description(self) -> str:
        return "获取B站当前热门视频，了解流行趋势和热点话题"

    @property
    def schema(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer", "description": "页码，默认1"},
                        "limit": {"type": "integer", "description": "每页数量，默认20"},
                    },
                    "required": [],
                },
            },
        }

    async def execute(self, page: int = 1, limit: int = 20) -> Dict:
        if not self._bilibili_service:
            raise RuntimeError("bilibili_service 未初始化")

        logger.info(f"[工具] 获取热门视频: page={page}, limit={limit}")
        res = await self._bilibili_service.get_hot_videos(pn=page, ps=limit)
        if not res.get("success"):
            return {
                "type": "error",
                "tool": self.name,
                "error": f"获取热门视频失败: {res.get('error')}",
            }

        return {"type": "tool_result", "tool": self.name, "data": res.get("data")}
