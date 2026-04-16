"""
数据源适配器模块

提供向后兼容的适配器层，统一现有代码到新的数据源架构。
让现有代码可以逐步迁移到新架构，无需大规模重构。

设计模式:
    - 适配器模式: 将新接口适配到旧接口
    - 门面模式: 提供统一的高层接口
"""

from typing import Any, Dict

from src.backend.services.data_sources.exceptions import UnsupportedPlatformError
from src.backend.services.data_sources.factory import DataSourceFactory
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class DataSourceAdapter:
    """
    数据源适配器类

    提供统一的数据访问接口，自动识别平台并调用对应的数据源。
    向后兼容现有代码，同时支持多平台扩展。

    核心功能:
        - URL自动识别平台
        - 统一的响应格式
        - 向后兼容旧接口
        - 错误处理和日志记录

    Usage:
        # 自动识别平台
        adapter = DataSourceAdapter()
        result = adapter.get_video_info("https://www.bilibili.com/video/BV1xx")

        # YouTube URL（未来）
        result = adapter.get_video_info("https://www.youtube.com/watch?v=xxx")

        # B站特定功能
        result = adapter.get_article_content("https://www.bilibili.com/read/cv12345")
    """

    def __init__(self, default_platform: str = None):
        """
        初始化适配器

        Args:
            default_platform: 默认平台名称（可选）
                             当无法从URL识别平台时使用
        """
        self._default_platform = default_platform
        self._source_cache = {}  # 缓存数据源实例

        logger.info("数据源适配器已初始化")

    # ========== 视频相关方法 ==========

    async def get_video_info(self, url: str) -> Dict[str, Any]:
        """
        自动识别平台并获取视频信息

        Args:
            url: 视频URL

        Returns:
            Dict: 标准响应格式

        Example:
            >>> adapter = DataSourceAdapter()
            >>> result = await adapter.get_video_info(
            ...     "https://www.bilibili.com/video/BV1xx411c7mD"
            ... )
            >>> if result['success']:
            ...     print(result['data']['title'])
        """
        try:
            source = self._get_source_from_url(url)
            video_id = await source.extract_video_id(url)

            if not video_id:
                return {
                    "success": False,
                    "error": "无法从URL提取视频ID",
                    "platform": source.platform_name,
                }

            return await source.get_video_info(video_id)
        except UnsupportedPlatformError as e:
            logger.error(f"不支持的平台: {url}")
            return {"success": False, "error": str(e), "platform": None}
        except Exception as e:
            logger.error(f"获取视频信息失败 ({url}): {str(e)}")
            return {"success": False, "error": f"获取视频信息失败: {str(e)}", "platform": None}

    async def get_video_subtitles(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        获取视频字幕

        Args:
            url: 视频URL
            **kwargs: 平台特定参数

        Returns:
            Dict: 标准响应格式
        """
        try:
            source = self._get_source_from_url(url)
            video_id = await source.extract_video_id(url)

            if not video_id:
                return {
                    "success": False,
                    "error": "无法从URL提取视频ID",
                    "platform": source.platform_name,
                }

            return await source.get_video_subtitles(video_id, **kwargs)
        except Exception as e:
            logger.error(f"获取字幕失败 ({url}): {str(e)}")
            return {"success": False, "error": f"获取字幕失败: {str(e)}", "platform": None}

    async def get_video_comments(
        self, url: str, max_count: int = 100, sort_by: str = "hot", **kwargs
    ) -> Dict[str, Any]:
        """
        获取视频评论

        Args:
            url: 视频URL
            max_count: 最大评论数
            sort_by: 排序方式
            **kwargs: 平台特定参数

        Returns:
            Dict: 标准响应格式
        """
        try:
            source = self._get_source_from_url(url)
            video_id = await source.extract_video_id(url)

            if not video_id:
                return {
                    "success": False,
                    "error": "无法从URL提取视频ID",
                    "platform": source.platform_name,
                }

            return await source.get_video_comments(
                video_id, max_count=max_count, sort_by=sort_by, **kwargs
            )
        except Exception as e:
            logger.error(f"获取评论失败 ({url}): {str(e)}")
            return {"success": False, "error": f"获取评论失败: {str(e)}", "platform": None}

    async def get_video_danmaku(self, url: str, max_count: int = 1000, **kwargs) -> Dict[str, Any]:
        """
        获取视频弹幕

        Args:
            url: 视频URL
            max_count: 最大弹幕数
            **kwargs: 平台特定参数

        Returns:
            Dict: 标准响应格式
        """
        try:
            source = self._get_source_from_url(url)
            video_id = await source.extract_video_id(url)

            if not video_id:
                return {
                    "success": False,
                    "error": "无法从URL提取视频ID",
                    "platform": source.platform_name,
                }

            return await source.get_video_danmaku(video_id, max_count=max_count, **kwargs)
        except Exception as e:
            logger.error(f"获取弹幕失败 ({url}): {str(e)}")
            return {"success": False, "error": f"获取弹幕失败: {str(e)}", "platform": None}

    # ========== 用户相关方法 ==========

    async def get_user_info(self, url: str) -> Dict[str, Any]:
        """
        获取用户信息

        Args:
            url: 用户主页URL

        Returns:
            Dict: 标准响应格式
        """
        try:
            source = self._get_source_from_url(url)
            user_id = await source.extract_user_id(url)

            if not user_id:
                return {
                    "success": False,
                    "error": "无法从URL提取用户ID",
                    "platform": source.platform_name,
                }

            return await source.get_user_info(user_id)
        except Exception as e:
            logger.error(f"获取用户信息失败 ({url}): {str(e)}")
            return {"success": False, "error": f"获取用户信息失败: {str(e)}", "platform": None}

    async def get_user_videos(self, url: str, limit: int = 10) -> Dict[str, Any]:
        """
        获取用户投稿视频

        Args:
            url: 用户主页URL
            limit: 返回数量

        Returns:
            Dict: 标准响应格式
        """
        try:
            source = self._get_source_from_url(url)
            user_id = await source.extract_user_id(url)

            if not user_id:
                return {
                    "success": False,
                    "error": "无法从URL提取用户ID",
                    "platform": source.platform_name,
                }

            return await source.get_user_videos(user_id, limit=limit)
        except Exception as e:
            logger.error(f"获取用户视频失败 ({url}): {str(e)}")
            return {"success": False, "error": f"获取用户视频失败: {str(e)}", "platform": None}

    # ========== 搜索相关方法 ==========

    async def search_videos(
        self, keyword: str, platform: str = None, limit: int = 10
    ) -> Dict[str, Any]:
        """
        搜索视频

        Args:
            keyword: 搜索关键词
            platform: 平台名称（可选，默认使用B站）
            limit: 返回数量

        Returns:
            Dict: 标准响应格式
        """
        try:
            # 如果没有指定平台，使用默认平台
            if not platform:
                platform = self._default_platform or "bilibili"

            source = self._get_source_from_platform(platform)
            return await source.search_videos(keyword, limit=limit)
        except Exception as e:
            logger.error(f"搜索视频失败 ({keyword}): {str(e)}")
            return {"success": False, "error": f"搜索视频失败: {str(e)}", "platform": platform}

    async def search_users(
        self, keyword: str, platform: str = None, limit: int = 10
    ) -> Dict[str, Any]:
        """
        搜索用户

        Args:
            keyword: 搜索关键词
            platform: 平台名称（可选，默认使用B站）
            limit: 返回数量

        Returns:
            Dict: 标准响应格式
        """
        try:
            if not platform:
                platform = self._default_platform or "bilibili"

            source = self._get_source_from_platform(platform)
            return await source.search_users(keyword, limit=limit)
        except Exception as e:
            logger.error(f"搜索用户失败 ({keyword}): {str(e)}")
            return {"success": False, "error": f"搜索用户失败: {str(e)}", "platform": platform}

    # ========== 热门/推荐方法 ==========

    async def get_popular_videos(self, platform: str = None, limit: int = 10) -> Dict[str, Any]:
        """
        获取热门视频

        Args:
            platform: 平台名称（可选，默认使用B站）
            limit: 返回数量

        Returns:
            Dict: 标准响应格式
        """
        try:
            if not platform:
                platform = self._default_platform or "bilibili"

            source = self._get_source_from_platform(platform)
            return await source.get_popular_videos(limit=limit)
        except Exception as e:
            logger.error(f"获取热门视频失败: {str(e)}")
            return {"success": False, "error": f"获取热门视频失败: {str(e)}", "platform": platform}

    # ========== 辅助方法 ==========

    def _get_source_from_url(self, url: str):
        """
        从URL获取数据源（带缓存）

        Args:
            url: URL

        Returns:
            DataSource: 数据源实例
        """
        # 尝试从缓存获取
        platform = DataSourceFactory.get_platform_from_url(url)

        if platform and platform in self._source_cache:
            return self._source_cache[platform]

        # 创建新实例
        source = DataSourceFactory.create_from_url(url)

        # 缓存
        if platform:
            self._source_cache[platform] = source

        return source

    def _get_source_from_platform(self, platform: str):
        """
        从平台名称获取数据源（带缓存）

        Args:
            platform: 平台名称

        Returns:
            DataSource: 数据源实例
        """
        # 从缓存获取
        if platform in self._source_cache:
            return self._source_cache[platform]

        # 创建新实例
        source = DataSourceFactory.create_by_platform(platform)

        # 缓存
        self._source_cache[platform] = source

        return source

    def get_supported_platforms(self):
        """
        获取所有支持的平台

        Returns:
            List[str]: 平台名称列表
        """
        return DataSourceFactory.get_supported_platforms()

    def is_supported_url(self, url: str) -> bool:
        """
        检查URL是否支持

        Args:
            url: URL

        Returns:
            bool: 支持返回 True
        """
        return DataSourceFactory.is_supported_url(url)

    def clear_cache(self):
        """清空数据源缓存"""
        self._source_cache.clear()
        logger.info("适配器数据源缓存已清空")


# ========== 便捷函数 ==========


async def get_video_info_universal(url: str) -> Dict[str, Any]:
    """
    便捷函数：获取视频信息（自动识别平台）

    Args:
        url: 视频URL

    Returns:
        Dict: 标准响应格式

    Example:
        >>> result = await get_video_info_universal(
        ...     "https://www.bilibili.com/video/BV1xx411c7mD"
        ... )
    """
    adapter = DataSourceAdapter()
    return await adapter.get_video_info(url)


async def search_videos_universal(
    keyword: str, platform: str = "bilibili", limit: int = 10
) -> Dict[str, Any]:
    """
    便捷函数：搜索视频

    Args:
        keyword: 搜索关键词
        platform: 平台名称
        limit: 返回数量

    Returns:
        Dict: 标准响应格式

    Example:
        >>> result = await search_videos_universal("Python教程")
    """
    adapter = DataSourceAdapter()
    return await adapter.search_videos(keyword, platform, limit)
