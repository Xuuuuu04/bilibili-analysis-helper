"""
获取视频所属合集信息工具
"""

from typing import Dict

from src.backend.services.ai.toolkit.base_tool import BaseTool
from src.backend.utils.bilibili_helpers import extract_bvid
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class GetVideoSeriesTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_video_series"

    @property
    def description(self) -> str:
        return "获取视频所属的合集信息，用于系统性学习系列教程或了解完整的知识体系"

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

        logger.info(f"[工具] 获取视频合集: {bvid}")
        res = await self._bilibili_service.get_video_series(bvid)
        if not res.get("success"):
            return {
                "type": "error",
                "tool": self.name,
                "error": f"获取视频合集失败: {res.get('error')}",
            }

        return {"type": "tool_result", "tool": self.name, "data": res.get("data")}
