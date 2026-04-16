"""
B站排行榜服务

提供各分区视频排行榜功能
"""

from typing import Dict, Optional

from bilibili_api import RankType, rank

from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class RankService:
    """B站排行榜服务"""

    def __init__(self, credential=None):
        """
        初始化排行榜服务

        Args:
            credential: B站认证凭据（可选）
        """
        self.credential = credential

    async def get_rank_videos(self, type_: Optional[str] = None, day: int = 3) -> Dict:
        """
        获取排行榜视频

        Args:
            type_: 分区类型 (all, bangumi, guochuang, douga, music, dance, game, knowledge, tech, sports, car, fashion, ent, cinephile, life, food, animal, caricature)
            day: 时间范围 (3=三日, 7=周排行)

        Returns:
            排行榜视频数据
        """
        try:
            # 映射字符串到 RankType 枚举
            rank_type = self._parse_rank_type(type_)

            result = await rank.get_rank(type_=rank_type, day=3 if day == 3 else 7)

            videos = []
            for item in result.get("list", []):
                videos.append(
                    {
                        "bvid": item.get("bvid"),
                        "title": item.get("title"),
                        "author": item.get("owner", {}).get("name"),
                        "cover": item.get("pic"),
                        "view": item.get("stat", {}).get("view"),
                        "like": item.get("stat", {}).get("like"),
                        "duration": item.get("duration"),
                    }
                )

            return {
                "success": True,
                "data": {
                    "videos": videos,
                    "type": type_ or "all",
                    "day": day,
                    "total": len(videos),
                },
            }

        except Exception as e:
            logger.error(f"获取排行榜失败: {str(e)}")
            return {"success": False, "error": str(e)}

    def _parse_rank_type(self, type_str: str):
        """
        解析分区类型

        Args:
            type_str: 分区类型字符串

        Returns:
            RankType 枚举值
        """
        type_map = {
            "all": RankType.ALL,
            "bangumi": RankType.BANGUMI,
            "guochuang": RankType.GUOCHUANG,
            "douga": RankType.DOUGA,
            "music": RankType.MUSIC,
            "dance": RankType.DANCE,
            "game": RankType.GAME,
            "knowledge": RankType.KNOWLEDGE,
            "tech": RankType.TECH,
            "sports": RankType.SPORTS,
            "car": RankType.CAR,
            "fashion": RankType.FASHION,
            "ent": RankType.ENT,
            "cinephile": RankType.CINEPHILE,
            "life": RankType.LIFE,
            "food": RankType.FOOD,
            "animal": RankType.ANIMAL,
            "caricature": RankType.CARICATURE,
        }

        return type_map.get(type_str, RankType.ALL)
