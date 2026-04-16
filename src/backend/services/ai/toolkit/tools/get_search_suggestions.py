"""
获取B站搜索联想工具
"""

from typing import Dict

from src.backend.services.ai.toolkit.base_tool import BaseTool
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class GetSearchSuggestionsTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_search_suggestions"

    @property
    def description(self) -> str:
        return "获取搜索联想建议，优化搜索词以获得更精准的搜索结果"

    @property
    def schema(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {"keyword": {"type": "string", "description": "部分搜索关键词"}},
                    "required": ["keyword"],
                },
            },
        }

    async def execute(self, keyword: str) -> Dict:
        if not self._bilibili_service:
            raise RuntimeError("bilibili_service 未初始化")

        logger.info(f"[工具] 获取搜索联想: {keyword}")
        res = await self._bilibili_service.get_search_suggestions(keyword)
        if not res.get("success"):
            return {
                "type": "error",
                "tool": self.name,
                "error": f"获取搜索建议失败: {res.get('error')}",
            }

        return {"type": "tool_result", "tool": self.name, "data": res.get("data")}
