"""
获取B站每周精选优质视频工具
"""

from typing import Dict

from src.backend.services.ai.toolkit.base_tool import BaseTool
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class GetWeeklyHotVideosTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_weekly_hot_videos"

    @property
    def description(self) -> str:
        return "获取B站每周精选优质视频（每周必看）"

    @property
    def schema(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {"week": {"type": "integer", "description": "第几周，默认1"}},
                    "required": [],
                },
            },
        }

    async def execute(self, week: int = 1) -> Dict:
        if not self._bilibili_service:
            raise RuntimeError("bilibili_service 未初始化")

        logger.info(f"[工具] 获取每周必看: week={week}")
        res = await self._bilibili_service.get_weekly_hot_videos(week=week)
        if not res.get("success"):
            return {
                "type": "error",
                "tool": self.name,
                "error": f"获取每周必看失败: {res.get('error')}",
            }

        return {"type": "tool_result", "tool": self.name, "data": res.get("data")}
