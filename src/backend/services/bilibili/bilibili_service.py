"""
B站服务统一入口
整合所有B站相关服务，提供向后兼容的接口
"""

from typing import Optional

from src.backend.services.bilibili.content_service import ContentService
from src.backend.services.bilibili.credential_manager import CredentialManager
from src.backend.services.bilibili.search_service import SearchService
from src.backend.services.bilibili.user_service import UserService
from src.backend.services.bilibili.video_service import VideoService
from src.backend.utils.async_helpers import run_async
from src.backend.utils.bilibili_helpers import extract_article_id, extract_bvid, format_duration
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class BilibiliService:
    """
    B站服务统一入口类（向后兼容）

    整合所有B站相关服务，提供与原 bilibili_service.py 相同的接口
    """

    # 静态工具方法（保持向后兼容）
    extract_bvid = staticmethod(extract_bvid)
    extract_article_id = staticmethod(extract_article_id)
    run_async = staticmethod(run_async)

    def __init__(self):
        """初始化B站服务，整合所有子服务"""
        self._credential_manager = CredentialManager()

        # 初始化所有子服务，共享同一个凭据
        self.video = VideoService(credential=self._credential_manager.credential)
        self.user = UserService(credential=self._credential_manager.credential)
        self.search = SearchService(credential=self._credential_manager.credential)
        self.content = ContentService(credential=self._credential_manager.credential)

    def refresh_credential(self):
        """
        刷新登录凭据（从Config重新加载）

        更新所有子服务的凭据
        """
        self._credential_manager.refresh()

        # 更新所有子服务的凭据
        new_credential = self._credential_manager.credential
        self.video.credential = new_credential
        self.user.credential = new_credential
        self.search.credential = new_credential
        self.content.credential = new_credential

        logger.info("所有B站服务的凭据已刷新")

    @property
    def credential(self):
        """获取当前凭据对象（向后兼容）"""
        return self._credential_manager.credential

    async def check_credential_valid(self) -> bool:
        """检查凭据是否有效（向后兼容）"""
        return await self._credential_manager.check_valid()

    # ========== 视频相关方法（委托给 VideoService）==========

    async def get_video_info(self, bvid: str):
        """获取视频基本信息"""
        return await self.video.get_info(bvid)

    async def get_video_subtitles(self, bvid: str):
        """获取视频字幕"""
        return await self.video.get_subtitles(bvid)

    async def get_video_danmaku(self, bvid: str, limit: int = 1000):
        """获取视频弹幕"""
        return await self.video.get_danmaku(bvid, limit)

    async def get_video_comments(self, bvid: str, max_pages: int = 10, target_count: int = 100):
        """获取视频评论"""
        return await self.video.get_comments(bvid, max_pages, target_count)

    async def get_video_stats(self, bvid: str):
        """获取视频统计信息"""
        return await self.video.get_stats(bvid)

    async def get_related_videos(self, bvid: str):
        """获取相关推荐视频"""
        return await self.video.get_related(bvid)

    async def get_popular_videos(self):
        """获取热门推荐视频"""
        return await self.search.get_popular_videos()

    async def extract_video_frames(
        self, bvid: str, max_frames: Optional[int] = None, interval: Optional[int] = None
    ):
        """提取视频关键帧"""
        return await self.video.extract_frames(bvid, max_frames, interval)

    async def get_video_tags(self, bvid: str):
        """
        获取视频标签及详细信息

        Args:
            bvid: 视频BVID

        Returns:
            标准响应格式 {"success": bool, "data": dict, "error": str}
        """
        return await self.video.get_video_tags(bvid)

    async def get_video_series(self, bvid: str):
        """
        获取视频所属的合集信息（系列视频）

        Args:
            bvid: 视频BVID

        Returns:
            标准响应格式 {"success": bool, "data": dict, "error": str}
        """
        return await self.video.get_video_series(bvid)

    # ========== 用户相关方法（委托给 UserService）==========

    async def get_user_info(self, uid: int):
        """获取用户基本信息"""
        return await self.user.get_info(uid)

    async def get_user_recent_videos(self, uid: int, limit: int = 10):
        """获取用户最近投稿"""
        return await self.user.get_recent_videos(uid, limit)

    async def get_user_dynamics(self, uid: int, limit: int = 10):
        """
        获取用户的最新动态

        Args:
            uid: 用户UID
            limit: 获取动态数量

        Returns:
            标准响应格式 {"success": bool, "data": dict, "error": str}
        """
        return await self.user.get_user_dynamics(uid, limit)

    # ========== 搜索相关方法（委托给 SearchService）==========

    async def search_videos(self, keyword: str, limit: int = 20):
        """搜索视频"""
        return await self.search.search_videos(keyword, limit)

    async def search_users(self, keyword: str, limit: int = 5):
        """搜索用户"""
        return await self.search.search_users(keyword, limit)

    async def search_articles(self, keyword: str, limit: int = 5):
        """搜索专栏"""
        return await self.search.search_articles(keyword, limit)

    async def get_search_suggestions(self, keyword: str):
        """
        获取搜索建议（联想词）

        Args:
            keyword: 用户输入的部分关键词

        Returns:
            标准响应格式 {"success": bool, "data": list, "error": str}
        """
        return await self.search.get_search_suggestions(keyword)

    async def get_hot_search_keywords(self):
        """
        获取当前热搜关键词

        Returns:
            标准响应格式 {"success": bool, "data": list, "error": str}
        """
        return await self.search.get_hot_search_keywords()

    # ========== 内容相关方法（委托给 ContentService）==========

    async def get_article_content(self, cvid: int):
        """获取专栏文章内容"""
        return await self.content.get_article_content(cvid)

    async def get_opus_content(self, opus_id: int):
        """获取Opus动态内容"""
        return await self.content.get_opus_content(opus_id)

    # ========== 热门和排行榜相关方法 ==========

    async def get_hot_videos(self, pn: int = 1, ps: int = 20):
        """
        获取B站热门视频

        Args:
            pn: 页码，默认1
            ps: 每页数量，默认20

        Returns:
            标准响应格式 {"success": bool, "data": dict, "error": str}
        """
        try:
            from bilibili_api import hot

            result = await hot.get_hot_videos(pn=pn, ps=ps)
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"获取热门视频失败: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_hot_buzzwords(self, page_num: int = 1, page_size: int = 20):
        """
        获取B站热词图鉴

        Args:
            page_num: 页码，默认1
            page_size: 每页数量，默认20

        Returns:
            标准响应格式 {"success": bool, "data": dict, "error": str}
        """
        try:
            from bilibili_api import hot

            result = await hot.get_hot_buzzwords(page_num=page_num, page_size=page_size)

            # 提取热词列表，标准化数据格式
            buzzwords = []
            for item in result.get("list", []):
                buzzwords.append(
                    {
                        "keyword": item.get("keyword"),
                        "icon": item.get("icon"),
                        "score": item.get("score"),  # 热度分数
                        "type": item.get("type"),  # 类型标识
                    }
                )

            return {
                "success": True,
                "data": {"buzzwords": buzzwords, "total": len(buzzwords), "page": page_num},
            }
        except Exception as e:
            logger.error(f"获取热词图鉴失败: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_weekly_hot_videos(self, week: int = 1):
        """
        获取B站每周必看视频

        Args:
            week: 第几周，默认1

        Returns:
            标准响应格式 {"success": bool, "data": dict, "error": str}
        """
        try:
            from bilibili_api import hot

            result = await hot.get_weekly_hot_videos(week=week)
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"获取每周必看失败: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_history_popular_videos(self):
        """
        获取B站入站必刷视频

        Returns:
            标准响应格式 {"success": bool, "data": dict, "error": str}
        """
        try:
            from bilibili_api import hot

            result = await hot.get_history_popular_videos()
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"获取入站必刷失败: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_rank_videos(self, type_, day: int = 3):
        """
        获取B站视频排行榜

        Args:
            type_: 分区类型 (RankType枚举)
            day: 时间范围，3=三日排行，7=周排行

        Returns:
            标准响应格式 {"success": bool, "data": dict, "error": str}
        """
        try:
            from bilibili_api import rank

            result = await rank.get_rank(type_=type_, day=day)
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"获取排行榜失败: {str(e)}")
            return {"success": False, "error": str(e)}

    # ========== 辅助方法（保持向后兼容）==========

    def _format_duration(self, seconds: int) -> str:
        """格式化时长（向后兼容）"""
        return format_duration(seconds)
