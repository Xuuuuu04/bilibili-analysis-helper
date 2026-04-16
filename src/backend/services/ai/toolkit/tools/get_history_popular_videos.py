"""
获取B站入站必刷经典视频工具
"""

from typing import Dict

from src.backend.services.ai.toolkit.base_tool import BaseTool
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class GetHistoryPopularVideosTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_history_popular_videos"

    @property
    def description(self) -> str:
        return "获取B站入站必刷的经典视频列表"

    @property
    def schema(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        }

    async def execute(self) -> Dict:
        if not self._bilibili_service:
            raise RuntimeError("bilibili_service 未初始化")

        logger.info("[工具] 获取入站必刷")
        res = await self._bilibili_service.get_history_popular_videos()
        if not res.get("success"):
            return {
                "type": "error",
                "tool": self.name,
                "error": f"获取入站必刷失败: {res.get('error')}",
            }

        return {"type": "tool_result", "tool": self.name, "data": res.get("data")}
