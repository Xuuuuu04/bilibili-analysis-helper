"""
全网搜索工具（Exa）
"""

from typing import Dict

from src.backend.services.ai.ai_helpers import web_search_exa
from src.backend.services.ai.toolkit.base_tool import BaseTool
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class WebSearchTool(BaseTool):
    """Exa全网搜索工具"""

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "使用 Exa AI 进行全网深度搜索，获取最新资讯、技术文档或 B 站以外的补充信息"

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
                        "query": {
                            "type": "string",
                            "description": "搜索查询语句，建议使用自然语言描述你想要找的内容",
                        }
                    },
                    "required": ["query"],
                },
            },
        }

    async def execute(self, query: str) -> Dict:
        """
        执行全网搜索

        Args:
            query: 搜索查询

        Returns:
            Dict: 搜索结果
        """
        logger.info(f"[工具] 全网搜索: {query}")

        search_res = web_search_exa(query)

        if not search_res["success"]:
            return {
                "type": "error",
                "tool": self.name,
                "error": f"网络搜索失败: {search_res.get('error', 'Unknown error')}",
            }

        return {"type": "tool_result", "tool": self.name, "data": search_res["data"]}
