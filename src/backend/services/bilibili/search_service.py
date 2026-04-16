"""
B站搜索服务模块
提供视频、用户、专栏搜索功能
"""

from typing import Dict

from bilibili_api import search

from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class SearchService:
    """
    B站搜索服务类

    提供搜索相关的功能：视频、用户、专栏搜索
    """

    def __init__(self, credential=None):
        """
        初始化搜索服务

        Args:
            credential: B站登录凭据（可选）
        """
        self.credential = credential

    async def search_videos(self, keyword: str, limit: int = 20) -> Dict:
        """
        搜索视频

        Args:
            keyword: 搜索关键词
            limit: 返回结果数量

        Returns:
            {'success': bool, 'data': [视频列表]} 或 {'success': False, 'error': str}
        """
        try:
            # search.search_by_type 返回搜索结果
            res = await search.search_by_type(
                keyword,
                search_type=search.SearchObjectType.VIDEO,
                order_type=search.OrderVideo.TOTALRANK,  # 综合排序
                page_size=limit,
            )

            result_list = []
            for item in res.get("result", []):
                # 过滤掉非视频项（有时候会有广告）
                if item.get("type") != "video":
                    continue
                result_list.append(
                    {
                        "bvid": item.get("bvid"),
                        "title": (item.get("title") or "")
                        .replace('<em class="keyword">', "")
                        .replace("</em>", ""),  # 清理高亮标签
                        "author": item.get("author"),
                        "pic": (
                            "https:" + item.get("pic")
                            if item.get("pic", "").startswith("//")
                            else item.get("pic")
                        ),
                        "play": item.get("play"),
                        "duration": item.get("duration"),
                    }
                )
            return {"success": True, "data": result_list}
        except Exception as e:
            return {"success": False, "error": f"搜索视频失败: {str(e)}"}

    async def search_users(self, keyword: str, limit: int = 5) -> Dict:
        """
        根据关键词搜索用户

        Args:
            keyword: 搜索关键词
            limit: 返回结果数量

        Returns:
            {'success': bool, 'data': [用户列表]} 或 {'success': False, 'error': str}
        """
        try:
            res = await search.search_by_type(
                keyword, search_type=search.SearchObjectType.USER, page_size=limit
            )
            result_list = []
            for item in res.get("result", []):
                result_list.append(
                    {
                        "mid": item.get("mid"),
                        "name": (item.get("uname") or "")
                        .replace('<em class="keyword">', "")
                        .replace("</em>", ""),
                        "face": (
                            "https:" + item.get("upic")
                            if item.get("upic", "").startswith("//")
                            else item.get("upic")
                        ),
                        "level": item.get("level"),
                        "sign": item.get("usign"),
                    }
                )
            return {"success": True, "data": result_list}
        except Exception as e:
            return {"success": False, "error": f"搜索用户失败: {str(e)}"}

    async def search_articles(self, keyword: str, limit: int = 5) -> Dict:
        """
        根据关键词搜索专栏/Opus

        Args:
            keyword: 搜索关键词
            limit: 返回结果数量

        Returns:
            {'success': bool, 'data': [专栏列表]} 或 {'success': False, 'error': str}
        """
        try:
            res = await search.search_by_type(
                keyword, search_type=search.SearchObjectType.ARTICLE, page_size=limit
            )
            result_list = []
            for item in res.get("result", []):
                result_list.append(
                    {
                        "cvid": item.get("id"),
                        "title": (item.get("title") or "")
                        .replace('<em class="keyword">', "")
                        .replace("</em>", ""),
                        "author": item.get("author"),
                        "pic": (
                            "https:" + item.get("image_urls", [None])[0]
                            if item.get("image_urls")
                            else ""
                        ),
                    }
                )
            return {"success": True, "data": result_list}
        except Exception as e:
            return {"success": False, "error": f"搜索专栏失败: {str(e)}"}

    async def get_popular_videos(self) -> Dict:
        """
        获取热门推荐视频 (用于首页展示)

        Returns:
            {'success': bool, 'data': [视频列表]} 或 {'success': False, 'error': str}
        """
        try:
            # 修正：使用 hot 模块获取热门视频
            from bilibili_api import hot

            res = await hot.get_hot_videos(pn=1, ps=12)

            processed = []
            for item in res.get("list", []):
                processed.append(
                    {
                        "bvid": item.get("bvid"),
                        "title": item.get("title"),
                        "author": item.get("owner", {}).get("name"),
                        "cover": item.get("pic"),
                        "duration": item.get("duration"),
                        "duration_str": self._format_duration(item.get("duration", 0)),
                        "view": item.get("stat", {}).get("view", 0),
                    }
                )
            return {"success": True, "data": processed}
        except Exception as e:
            logger.warning(f"获取热门视频失败: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def _format_duration(seconds: int) -> str:
        """格式化时长"""
        if not seconds:
            return "00:00"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

    async def get_search_suggestions(self, keyword: str) -> Dict:
        """
        获取搜索建议（联想词）

        Args:
            keyword: 用户输入的部分关键词

        Returns:
            {'success': bool, 'data': [建议词列表]} 或 {'success': False, 'error': str}
        """
        try:
            suggestions = await search.get_suggest_keywords(keyword)
            return {"success": True, "data": suggestions}
        except Exception as e:
            logger.error(f"获取搜索建议失败: {str(e)}")
            return {"success": False, "error": f"获取搜索建议失败: {str(e)}"}

    async def get_hot_search_keywords(self) -> Dict:
        """
        获取当前热搜关键词

        Returns:
            {'success': bool, 'data': [热搜词列表]} 或 {'success': False, 'error': str}
        """
        try:
            hot_result = await search.get_hot_search_keywords()
            # 提取热搜关键词列表
            hot_keywords = []
            for item in hot_result.get("list", []):
                hot_keywords.append(
                    {
                        "keyword": item.get("keyword"),
                        "icon": item.get("icon"),
                        "hot": item.get("hot"),  # 热度值
                    }
                )
            return {"success": True, "data": hot_keywords}
        except Exception as e:
            logger.error(f"获取热搜关键词失败: {str(e)}")
            return {"success": False, "error": f"获取热搜关键词失败: {str(e)}"}
