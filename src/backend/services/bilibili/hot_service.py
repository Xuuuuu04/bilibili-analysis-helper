"""
B站热门内容服务

提供热门视频、热词图鉴等功能
"""

from typing import Dict

from bilibili_api import hot

from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class HotService:
    """B站热门内容服务"""

    def __init__(self, credential=None):
        """
        初始化热门内容服务

        Args:
            credential: B站认证凭据（可选）
        """
        self.credential = credential

    async def get_hot_videos(self, pn: int = 1, ps: int = 20) -> Dict:
        """
        获取热门视频

        Args:
            pn: 页码
            ps: 每页数量

        Returns:
            热门视频数据
        """
        try:
            result = await hot.get_hot_videos(pn=pn, ps=ps)

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
                "data": {"videos": videos, "total": result.get("num", 0), "page": pn},
            }

        except Exception as e:
            logger.error(f"获取热门视频失败: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_hot_buzzwords(self, page_num: int = 1, page_size: int = 20) -> Dict:
        """
        获取热词图鉴

        Args:
            page_num: 页码
            page_size: 每页数量

        Returns:
            热词数据
        """
        try:
            result = await hot.get_hot_buzzwords(page_num=page_num, page_size=page_size)

            buzzwords = []
            for item in result.get("list", []):
                buzzwords.append(
                    {
                        "keyword": item.get("keyword"),
                        "icon": item.get("icon"),
                        "score": item.get("score"),
                        "type": item.get("type"),
                    }
                )

            return {
                "success": True,
                "data": {"buzzwords": buzzwords, "total": len(buzzwords), "page": page_num},
            }

        except Exception as e:
            logger.error(f"获取热词图鉴失败: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_weekly_hot_videos(self, week: int = 1) -> Dict:
        """
        获取每周必看

        Args:
            week: 周数

        Returns:
            每周必看视频数据
        """
        try:
            result = await hot.get_weekly_hot_videos(week=week)

            return {"success": True, "data": result}

        except Exception as e:
            logger.error(f"获取每周必看失败: {str(e)}")
            return {"success": False, "error": str(e)}
