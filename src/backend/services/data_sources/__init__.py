"""
数据源抽象层

提供统一的多平台数据访问接口，支持视频、用户、评论等数据获取。

模块结构:
    base.py - DataSource 抽象基类
    exceptions.py - 数据源专用异常
    bilibili_source.py - B站数据源实现
    youtube_source.py - YouTube数据源实现（预留）
    factory.py - 数据源工厂
    adapter.py - 适配器层

使用示例:
    # 方式1: 使用适配器（推荐，自动识别平台）
    from src.backend.services.data_sources import DataSourceAdapter

    adapter = DataSourceAdapter()
    result = await adapter.get_video_info("https://www.bilibili.com/video/BV1xx")

    # 方式2: 使用工厂创建数据源
    from src.backend.services.data_sources import DataSourceFactory

    source = DataSourceFactory.create_from_url("https://www.bilibili.com/video/BV1xx")
    video_id = await source.extract_video_id(url)
    result = await source.get_video_info(video_id)

    # 方式3: 便捷函数
    from src.backend.services.data_sources import get_video_info_universal

    result = await get_video_info_universal("https://www.bilibili.com/video/BV1xx")

支持的平台:
    - bilibili (B站) - 完整支持
    - youtube (YouTube) - 预留接口，暂未实现

扩展新平台:
    1. 继承 DataSource 基类
    2. 实现所有抽象方法
    3. 注册到 DataSourceFactory

    from src.backend.services.data_sources import DataSource, DataSourceFactory

    class DouyinSource(DataSource):
        @property
        def platform_name(self) -> str:
            return "douyin"

        # 实现其他方法...

    DataSourceFactory.register_source('douyin.com', DouyinSource)
"""

# 导入基类和接口
from src.backend.services.data_sources.adapter import (
    DataSourceAdapter,
    get_video_info_universal,
    search_videos_universal,
)
from src.backend.services.data_sources.base import ContentType, DataSource

# 导入具体数据源实现
from src.backend.services.data_sources.bilibili_source import BilibiliSource

# 导入异常类
from src.backend.services.data_sources.exceptions import (
    APIError,
    ArticleNotFoundError,
    AuthenticationError,
    ContentAccessDeniedError,
    CredentialRequiredError,
    DataSourceError,
    FeatureNotSupportedError,
    InvalidParameterError,
    InvalidURLError,
    NetworkError,
    ParseError,
    RateLimitError,
    UnsupportedPlatformError,
    UserNotFoundError,
    VideoNotFoundError,
)

# 导入工厂和适配器
from src.backend.services.data_sources.factory import DataSourceFactory
from src.backend.services.data_sources.youtube_source import YouTubeSource

# 版本信息
__version__ = "1.0.0"
__author__ = "BiliInsight Team"

# 公共接口导出
__all__ = [
    # 基类和接口
    "DataSource",
    "ContentType",
    # 异常类
    "DataSourceError",
    "UnsupportedPlatformError",
    "InvalidURLError",
    "VideoNotFoundError",
    "UserNotFoundError",
    "ArticleNotFoundError",
    "APIError",
    "AuthenticationError",
    "RateLimitError",
    "FeatureNotSupportedError",
    "ContentAccessDeniedError",
    "CredentialRequiredError",
    "InvalidParameterError",
    "NetworkError",
    "ParseError",
    # 数据源实现
    "BilibiliSource",
    "YouTubeSource",
    # 工厂和适配器
    "DataSourceFactory",
    "DataSourceAdapter",
    "get_video_info_universal",
    "search_videos_universal",
]
