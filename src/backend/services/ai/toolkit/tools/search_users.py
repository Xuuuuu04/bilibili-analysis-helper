"""
搜索B站UP主工具
"""

from typing import Dict

from src.backend.services.ai.toolkit.base_tool import BaseTool
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class SearchUsersTool(BaseTool):
    """搜索B站UP主工具"""

    @property
    def name(self) -> str:
        return "search_users"

    @property
    def description(self) -> str:
        return "根据关键词/昵称模糊搜索 B 站 UP 主"

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
                        "keyword": {"type": "string", "description": "UP 主昵称或相关关键词"}
                    },
                    "required": ["keyword"],
                },
            },
        }

    async def execute(self, keyword: str, limit: int = 5) -> Dict:
        """
        执行搜索

        Args:
            keyword: 搜索关键词
            limit: 返回数量限制

        Returns:
            Dict: 搜索结果
        """
        if not self._bilibili_service:
            raise RuntimeError("bilibili_service 未初始化")

        logger.info(f"[工具] 搜索用户: {keyword}")

        search_res = await self._bilibili_service.search_users(keyword, limit=limit)

        if not search_res["success"]:
            return {
                "type": "error",
                "tool": self.name,
                "error": f"搜索用户失败: {search_res.get('error', 'Unknown error')}",
            }

        return {"type": "tool_result", "tool": self.name, "data": search_res["data"]}
