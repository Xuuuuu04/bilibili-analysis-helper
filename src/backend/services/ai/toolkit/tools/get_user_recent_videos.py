"""
获取UP主最近投稿工具
"""

from typing import Dict

from src.backend.services.ai.toolkit.base_tool import BaseTool
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class GetUserRecentVideosTool(BaseTool):
    """获取UP主最近投稿工具"""

    @property
    def name(self) -> str:
        return "get_user_recent_videos"

    @property
    def description(self) -> str:
        return "获取指定 UP 主的最近投稿视频列表"

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
                        "limit": {
                            "type": "integer",
                            "description": "获取视频的数量，默认 10",
                            "default": 10,
                        },
                    },
                    "required": ["mid"],
                },
            },
        }

    async def execute(self, mid: int, limit: int = 10) -> Dict:
        """
        执行获取

        Args:
            mid: UP主UID
            limit: 返回数量限制

        Returns:
            Dict: 视频列表
        """
        if not self._bilibili_service:
            raise RuntimeError("bilibili_service 未初始化")

        logger.info(f"[工具] 获取用户投稿: mid={mid}, limit={limit}")

        v_res = await self._bilibili_service.get_user_recent_videos(mid, limit=limit)

        if not v_res["success"]:
            return {
                "type": "error",
                "tool": self.name,
                "error": f"获取用户作品失败: {v_res.get('error', 'Unknown error')}",
            }

        return {"type": "tool_result", "tool": self.name, "data": v_res["data"]}
