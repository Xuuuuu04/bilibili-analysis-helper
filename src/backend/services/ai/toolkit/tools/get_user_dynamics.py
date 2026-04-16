"""
获取UP主最新动态工具
"""

from typing import Dict

from src.backend.services.ai.toolkit.base_tool import BaseTool
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class GetUserDynamicsTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_user_dynamics"

    @property
    def description(self) -> str:
        return "获取 UP 主的最新动态，了解其日常运营、社交互动和最新想法"

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
                        "mid": {"type": "integer", "description": "UP 主的 UID (mid)"},
                        "limit": {"type": "integer", "description": "获取动态的数量，默认 10"},
                    },
                    "required": ["mid"],
                },
            },
        }

    async def execute(self, mid: int, limit: int = 10) -> Dict:
        if not self._bilibili_service:
            raise RuntimeError("bilibili_service 未初始化")

        logger.info(f"[工具] 获取用户动态: mid={mid}, limit={limit}")
        res = await self._bilibili_service.get_user_dynamics(mid, limit=limit)
        if not res.get("success"):
            return {
                "type": "error",
                "tool": self.name,
                "error": f"获取用户动态失败: {res.get('error')}",
            }

        return {"type": "tool_result", "tool": self.name, "data": res.get("data")}
