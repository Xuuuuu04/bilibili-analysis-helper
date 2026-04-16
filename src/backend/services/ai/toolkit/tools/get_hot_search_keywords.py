"""
获取B站热搜关键词工具
"""

from typing import Dict

from src.backend.services.ai.toolkit.base_tool import BaseTool
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class GetHotSearchKeywordsTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_hot_search_keywords"

    @property
    def description(self) -> str:
        return "获取当前 B 站热搜关键词，把握热点趋势和用户关注焦点"

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

        logger.info("[工具] 获取热搜关键词")
        res = await self._bilibili_service.get_hot_search_keywords()
        if not res.get("success"):
            return {
                "type": "error",
                "tool": self.name,
                "error": f"获取热搜关键词失败: {res.get('error')}",
            }

        return {"type": "tool_result", "tool": self.name, "data": res.get("data")}
