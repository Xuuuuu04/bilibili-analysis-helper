"""
获取视频标签信息工具
"""

from typing import Dict

from src.backend.services.ai.toolkit.base_tool import BaseTool
from src.backend.utils.bilibili_helpers import extract_bvid
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class GetVideoTagsTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_video_tags"

    @property
    def description(self) -> str:
        return "获取视频的标签信息，了解视频的分类、主题和关联内容"

    @property
    def schema(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {"bvid": {"type": "string", "description": "视频的 BV 号"}},
                    "required": ["bvid"],
                },
            },
        }

    async def execute(self, bvid: str) -> Dict:
        if not self._bilibili_service:
            raise RuntimeError("bilibili_service 未初始化")

        if bvid and ("bilibili.com" in bvid or "http" in bvid):
            bvid = extract_bvid(bvid) or bvid

        logger.info(f"[工具] 获取视频标签: {bvid}")
        res = await self._bilibili_service.get_video_tags(bvid)
        if not res.get("success"):
            return {
                "type": "error",
                "tool": self.name,
                "error": f"获取视频标签失败: {res.get('error')}",
            }

        return {"type": "tool_result", "tool": self.name, "data": res.get("data")}
