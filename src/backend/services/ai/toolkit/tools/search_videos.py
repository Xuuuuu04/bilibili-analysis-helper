"""
搜索B站视频工具
"""

from typing import Dict

from src.backend.services.ai.toolkit.base_tool import BaseTool
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class SearchVideosTool(BaseTool):
    """搜索B站视频工具"""

    @property
    def name(self) -> str:
        return "search_videos"

    @property
    def description(self) -> str:
        return "搜索 B 站视频以获取相关研究素材"

    @property
    def schema(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {"keyword": {"type": "string", "description": "搜索关键词"}},
                    "required": ["keyword"],
                },
            },
        }

    async def execute(self, keyword: str, limit: int = 30) -> Dict:
        """
        执行搜索

        Args:
            keyword: 搜索关键词
            limit: 返回数量限制 (深度研究建议提供更多选项)

        Returns:
            Dict: 搜索结果
        """
        if not self._bilibili_service:
            raise RuntimeError("bilibili_service 未初始化")

        logger.info(f"[工具] 搜索视频: {keyword}")

        search_res = await self._bilibili_service.search_videos(keyword, limit=limit)

        if not search_res["success"]:
            return {
                "type": "error",
                "tool": self.name,
                "error": f"搜索失败: {search_res.get('error', 'Unknown error')}",
            }

        # 返回前 20 个结果给 AI，提供足够的选择余地
        result_data = (
            search_res["data"][:20] if len(search_res["data"]) > 20 else search_res["data"]
        )

        return {"type": "tool_result", "tool": self.name, "data": result_data}
