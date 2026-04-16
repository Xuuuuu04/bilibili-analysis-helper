"""
数据源工厂模块

提供数据源的创建、注册和管理功能。
支持根据URL自动识别平台并创建对应的数据源实例。

设计模式:
    - 工厂模式: 根据平台创建数据源实例
    - 注册表模式: 动态注册新平台
    - 单例模式: 共享数据源实例
"""

from typing import Dict, List, Optional, Type
from urllib.parse import urlparse

from src.backend.services.data_sources.base import DataSource
from src.backend.services.data_sources.bilibili_source import BilibiliSource
from src.backend.services.data_sources.exceptions import UnsupportedPlatformError
from src.backend.services.data_sources.youtube_source import YouTubeSource
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class DataSourceFactory:
    """
    数据源工厂类

    负责根据URL或平台名称创建对应的数据源实例。
    支持动态注册新平台，遵循开闭原则。

    Usage:
        # 根据URL自动创建
        source = DataSourceFactory.create_from_url("https://www.bilibili.com/video/BV1xx")

        # 根据平台名称创建
        source = DataSourceFactory.create_by_platform("bilibili")

        # 注册自定义平台
        DataSourceFactory.register_source("douyin.com", DouyinSource)
    """

    # 类变量：已注册的数据源
    # 格式: {域名: 数据源类}
    _registered_sources: Dict[str, Type[DataSource]] = {
        # B站
        "bilibili.com": BilibiliSource,
        "b23.tv": BilibiliSource,
        "m.bilibili.com": BilibiliSource,
        # YouTube
        "youtube.com": YouTubeSource,
        "youtu.be": YouTubeSource,
        "m.youtube.com": YouTubeSource,
    }

    # 类变量：实例缓存（可选，避免重复创建）
    _instance_cache: Dict[str, DataSource] = {}

    @classmethod
    def register_source(cls, domain: str, source_class: Type[DataSource]):
        """
        注册新的数据源

        Args:
            domain: 域名（如 'douyin.com'）
            source_class: 数据源类（必须继承自 DataSource）

        Raises:
            TypeError: 如果 source_class 不是 DataSource 的子类

        Example:
            >>> from src.backend.services.data_sources.douyin_source import DouyinSource
            >>> DataSourceFactory.register_source('douyin.com', DouyinSource)
        """
        if not issubclass(source_class, DataSource):
            raise TypeError(f"{source_class.__name__} 必须继承自 DataSource")

        cls._registered_sources[domain.lower()] = source_class
        logger.info(f"已注册数据源: {domain} -> {source_class.__name__}")

    @classmethod
    def unregister_source(cls, domain: str):
        """
        注销数据源

        Args:
            domain: 域名
        """
        if domain.lower() in cls._registered_sources:
            source_class = cls._registered_sources.pop(domain.lower())
            logger.info(f"已注销数据源: {domain} ({source_class.__name__})")
        else:
            logger.warning(f"尝试注销不存在的数据源: {domain}")

    @classmethod
    def create_from_url(cls, url: str, use_cache: bool = True) -> DataSource:
        """
        根据URL创建数据源

        自动识别URL中的域名，创建对应平台的数据源实例。

        Args:
            url: 视频/用户/文章URL
            use_cache: 是否使用缓存的实例（默认True）

        Returns:
            DataSource: 数据源实例

        Raises:
            UnsupportedPlatformError: 不支持的平台

        Example:
            >>> source = DataSourceFactory.create_from_url(
            ...     "https://www.bilibili.com/video/BV1xx411c7mD"
            ... )
            >>> print(source.platform_name)  # 输出: bilibili
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # 移除 www. 前缀以便匹配
            if domain.startswith("www."):
                domain = domain[4:]

            # 查找匹配的数据源
            source_class = None
            matched_domain = None

            for registered_domain, registered_class in cls._registered_sources.items():
                if registered_domain in domain:
                    source_class = registered_class
                    matched_domain = registered_domain
                    break

            if not source_class:
                raise UnsupportedPlatformError(url)

            # 检查缓存
            cache_key = f"{matched_domain}:{source_class.__name__}"
            if use_cache and cache_key in cls._instance_cache:
                logger.debug(f"使用缓存的数据源实例: {cache_key}")
                return cls._instance_cache[cache_key]

            # 创建新实例
            logger.info(f"创建数据源: {matched_domain} -> {source_class.__name__}")
            source = source_class()

            # 缓存实例
            if use_cache:
                cls._instance_cache[cache_key] = source

            return source

        except UnsupportedPlatformError:
            raise
        except Exception as e:
            logger.error(f"从URL创建数据源失败 ({url}): {str(e)}")
            raise UnsupportedPlatformError(url) from e

    @classmethod
    def create_by_platform(cls, platform: str, use_cache: bool = True, **kwargs) -> DataSource:
        """
        根据平台名称创建数据源

        Args:
            platform: 平台名称（如 'bilibili', 'youtube'）
            use_cache: 是否使用缓存的实例（默认True）
            **kwargs: 传递给数据源构造函数的参数

        Returns:
            DataSource: 数据源实例

        Raises:
            UnsupportedPlatformError: 不支持的平台

        Example:
            >>> source = DataSourceFactory.create_by_platform('bilibili')
            >>> print(source.platform_name)  # 输出: bilibili
        """
        # 查找对应平台的数据源类
        source_class = None

        # 平台名称到域名的映射
        platform_domain_map = {
            "bilibili": "bilibili.com",
            "b23": "b23.tv",
            "youtube": "youtube.com",
            "youtu.be": "youtu.be",
        }

        # 规范化平台名称
        platform = platform.lower().strip()

        # 如果是域名，直接查找
        if "." in platform:
            domain = platform
            for registered_domain, registered_class in cls._registered_sources.items():
                if registered_domain in domain:
                    source_class = registered_class
                    break
        else:
            # 使用映射表
            domain = platform_domain_map.get(platform)
            if domain:
                source_class = cls._registered_sources.get(domain)

        if not source_class:
            # 遍历所有已注册的数据源，查找匹配的平台名称
            for registered_class in cls._registered_sources.values():
                try:
                    # 创建临时实例检查平台名称
                    temp_instance = registered_class(**kwargs)
                    if temp_instance.platform_name == platform:
                        source_class = registered_class
                        break
                except Exception:
                    continue

        if not source_class:
            raise UnsupportedPlatformError(
                f"不支持的平台: {platform} " f"(已支持: {cls.get_supported_platforms()})"
            )

        # 检查缓存
        cache_key = f"{platform}:{source_class.__name__}"
        if use_cache and cache_key in cls._instance_cache:
            logger.debug(f"使用缓存的数据源实例: {cache_key}")
            return cls._instance_cache[cache_key]

        # 创建新实例
        logger.info(f"创建数据源: {platform} -> {source_class.__name__}")
        source = source_class(**kwargs)

        # 缓存实例
        if use_cache:
            cls._instance_cache[cache_key] = source

        return source

    @classmethod
    def get_supported_platforms(cls) -> List[str]:
        """
        获取所有支持的平台名称列表

        Returns:
            List[str]: 平台名称列表

        Example:
            >>> platforms = DataSourceFactory.get_supported_platforms()
            >>> print(platforms)  # ['bilibili', 'youtube', ...]
        """
        platforms = set()

        for source_class in cls._registered_sources.values():
            try:
                # 创建临时实例获取平台名称
                temp_instance = source_class()
                platforms.add(temp_instance.platform_name)
            except Exception:
                continue

        return sorted(list(platforms))

    @classmethod
    def get_supported_domains(cls) -> List[str]:
        """
        获取所有支持的域名列表

        Returns:
            List[str]: 域名列表

        Example:
            >>> domains = DataSourceFactory.get_supported_domains()
            >>> print(domains)  # ['bilibili.com', 'b23.tv', 'youtube.com', ...]
        """
        return sorted(list(cls._registered_sources.keys()))

    @classmethod
    def is_supported_url(cls, url: str) -> bool:
        """
        检查URL是否支持

        Args:
            url: 待检查的URL

        Returns:
            bool: 支持返回 True

        Example:
            >>> if DataSourceFactory.is_supported_url("https://www.bilibili.com/..."):
            ...     print("支持此URL")
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            for registered_domain in cls._registered_sources:
                if registered_domain in domain:
                    return True

            # 检查是否是直接的 BVID（无域名）
            import re

            if re.match(r"^BV[a-zA-Z0-9]{10}$", url.strip()):
                return True

            return False
        except Exception:
            return False

    @classmethod
    def clear_cache(cls):
        """
        清空实例缓存

        当需要刷新数据源实例时使用（如更新凭据）
        """
        cls._instance_cache.clear()
        logger.info("数据源实例缓存已清空")

    @classmethod
    def get_platform_from_url(cls, url: str) -> Optional[str]:
        """
        从URL提取平台名称

        Args:
            url: URL

        Returns:
            Optional[str]: 平台名称，不支持返回 None

        Example:
            >>> platform = DataSourceFactory.get_platform_from_url(
            ...     "https://www.bilibili.com/video/BV1xx"
            ... )
            >>> print(platform)  # 输出: bilibili
        """
        try:
            source = cls.create_from_url(url, use_cache=False)
            return source.platform_name
        except Exception:
            return None
