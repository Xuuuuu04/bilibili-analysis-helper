"""
获取B站排行榜工具
"""

from typing import Dict

from src.backend.services.ai.toolkit.base_tool import BaseTool
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class GetRankVideosTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_rank_videos"

    @property
    def description(self) -> str:
        return "获取指定分区的视频排行榜"

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
                        "category": {
                            "type": "string",
                            "description": "分区类型，如 knowledge、technology、game、music 等",
                        },
                        "day": {"type": "integer", "description": "时间范围：3=三日排行，7=周排行"},
                    },
                    "required": ["category"],
                },
            },
        }

    async def execute(self, category: str, day: int = 3) -> Dict:
        if not self._bilibili_service:
            raise RuntimeError("bilibili_service 未初始化")

        from bilibili_api import rank

        category_map = {
            "knowledge": rank.RankType.Knowledge,
            "technology": rank.RankType.Technology,
            "game": rank.RankType.Game,
            "music": rank.RankType.Music,
            "douga": rank.RankType.Douga,
            "dance": rank.RankType.Dance,
            "life": rank.RankType.Life,
            "food": rank.RankType.Food,
            "fashion": rank.RankType.Fashion,
            "ent": rank.RankType.Ent,
            "cinephile": rank.RankType.Cinephile,
            "sports": rank.RankType.Sports,
            "car": rank.RankType.Car,
            "animal": rank.RankType.Animal,
        }

        rank_type = category_map.get((category or "").lower())
        if not rank_type:
            return {
                "type": "error",
                "tool": self.name,
                "error": f"不支持的分区类型: {category}",
            }

        logger.info(f"[工具] 获取排行榜: category={category}, day={day}")
        res = await self._bilibili_service.get_rank_videos(type_=rank_type, day=day)
        if not res.get("success"):
            return {
                "type": "error",
                "tool": self.name,
                "error": f"获取排行榜失败: {res.get('error')}",
            }

        return {"type": "tool_result", "tool": self.name, "data": res.get("data")}
