"""
获取B站热词图鉴工具
"""

from typing import Dict

from src.backend.services.ai.toolkit.base_tool import BaseTool
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class GetHotBuzzwordsTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_hot_buzzwords"

    @property
    def description(self) -> str:
        return "获取B站热词图鉴，了解网络流行语、梗文化和社区热点话题"

    @property
    def schema(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {"page": {"type": "integer", "description": "页码，默认1"}},
                    "required": [],
                },
            },
        }

    async def execute(self, page: int = 1) -> Dict:
        if not self._bilibili_service:
            raise RuntimeError("bilibili_service 未初始化")

        logger.info(f"[工具] 获取热词图鉴: page={page}")
        res = await self._bilibili_service.get_hot_buzzwords(page_num=page, page_size=20)
        if not res.get("success"):
            return {
                "type": "error",
                "tool": self.name,
                "error": f"获取热词图鉴失败: {res.get('error')}",
            }

        return {"type": "tool_result", "tool": self.name, "data": res.get("data")}
