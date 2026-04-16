"""
数据源抽象基类模块

定义了所有数据源必须实现的统一接口，确保多平台数据访问的一致性。
遵循依赖倒置原则，高层模块依赖于抽象而非具体实现。

设计原则:
    - 开闭原则: 对扩展开放，对修改关闭
    - 里氏替换: 所有数据源可互相替换
    - 接口隔离: 接口精简，职责单一
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional


class ContentType(Enum):
    """内容类型枚举"""

    VIDEO = "video"
    ARTICLE = "article"
    DYNAMIC = "dynamic"
    USER = "user"
    COMMENT = "comment"
    SEARCH = "search"


class DataSource(ABC):
    """
    数据源抽象基类

    所有平台数据源必须实现此接口，确保统一的数据访问方式。
    支持视频、文章、用户、评论等多种内容类型的获取。
    """

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """
        平台名称

        Returns:
            str: 平台唯一标识符 (如 'bilibili', 'youtube', 'douyin')
        """
        pass

    @property
    @abstractmethod
    def supported_domains(self) -> List[str]:
        """
        支持的域名列表

        Returns:
            List[str]: 该平台支持的所有域名 (如 ['bilibili.com', 'b23.tv'])
        """
        pass

    # ========== URL 解析方法 ==========

    @abstractmethod
    async def extract_video_id(self, url: str) -> Optional[str]:
        """
        从URL提取视频ID

        Args:
            url: 视频URL

        Returns:
            Optional[str]: 视频ID，提取失败返回 None

        Raises:
            InvalidURLError: URL格式不正确
        """
        pass

    @abstractmethod
    async def extract_user_id(self, url: str) -> Optional[str]:
        """
        从URL提取用户ID

        Args:
            url: 用户主页URL

        Returns:
            Optional[str]: 用户ID，提取失败返回 None
        """
        pass

    @abstractmethod
    async def extract_article_id(self, url: str) -> Optional[str]:
        """
        从URL提取文章ID

        Args:
            url: 文章URL

        Returns:
            Optional[str]: 文章ID，提取失败返回 None
        """
        pass

    @abstractmethod
    def is_supported_url(self, url: str) -> bool:
        """
        检查URL是否被支持

        Args:
            url: 待检查的URL

        Returns:
            bool: 支持返回 True，否则返回 False
        """
        pass

    # ========== 视频相关方法 ==========

    @abstractmethod
    async def get_video_info(self, video_id: str) -> Dict[str, Any]:
        """
        获取视频基本信息

        Args:
            video_id: 视频ID

        Returns:
            Dict: 标准响应格式
            {
                'success': bool,
                'data': {
                    'id': str,           # 视频ID
                    'title': str,        # 标题
                    'description': str,  # 描述
                    'duration': int,     # 时长(秒)
                    'author': str,       # 作者
                    'view_count': int,   # 观看数
                    'cover_url': str,    # 封面URL
                    'publish_time': int, # 发布时间戳
                    ...
                },
                'error': str,
                'platform': str
            }

        Raises:
            VideoNotFoundError: 视频不存在
            APIError: API调用失败
        """
        pass

    @abstractmethod
    async def get_video_subtitles(self, video_id: str, **kwargs) -> Dict[str, Any]:
        """
        获取视频字幕

        Args:
            video_id: 视频ID
            **kwargs: 平台特定参数

        Returns:
            Dict: 标准响应格式
            {
                'success': bool,
                'data': {
                    'has_subtitle': bool,
                    'subtitles': [
                        {'text': str, 'start_time': float, 'end_time': float}
                    ]
                },
                'error': str,
                'platform': str
            }
        """
        pass

    @abstractmethod
    async def get_video_comments(
        self, video_id: str, max_count: int = 100, sort_by: str = "hot", **kwargs
    ) -> Dict[str, Any]:
        """
        获取视频评论

        Args:
            video_id: 视频ID
            max_count: 最大评论数
            sort_by: 排序方式 ('hot' 或 'time')
            **kwargs: 平台特定参数

        Returns:
            Dict: 标准响应格式
            {
                'success': bool,
                'data': {
                    'comments': [
                        {
                            'content': str,
                            'author': str,
                            'like_count': int,
                            'publish_time': int
                        }
                    ],
                    'total': int
                },
                'error': str,
                'platform': str
            }
        """
        pass

    @abstractmethod
    async def get_video_danmaku(
        self, video_id: str, max_count: int = 1000, **kwargs
    ) -> Dict[str, Any]:
        """
        获取视频弹幕（如果平台支持）

        Args:
            video_id: 视频ID
            max_count: 最大弹幕数
            **kwargs: 平台特定参数

        Returns:
            Dict: 标准响应格式
            {
                'success': bool,
                'data': {
                    'has_danmaku': bool,
                    'danmaku': [
                        {'text': str, 'time': float, 'color': str}
                    ]
                },
                'error': str,
                'platform': str
            }
        """
        pass

    @abstractmethod
    async def get_video_tags(self, video_id: str) -> Dict[str, Any]:
        """
        获取视频标签

        Args:
            video_id: 视频ID

        Returns:
            Dict: 标准响应格式
            {
                'success': bool,
                'data': {
                    'tags': [
                        {'name': str, 'id': str}
                    ]
                },
                'error': str,
                'platform': str
            }
        """
        pass

    @abstractmethod
    async def get_related_videos(self, video_id: str, **kwargs) -> Dict[str, Any]:
        """
        获取相关推荐视频

        Args:
            video_id: 视频ID
            **kwargs: 平台特定参数

        Returns:
            Dict: 标准响应格式
            {
                'success': bool,
                'data': {
                    'videos': [
                        {
                            'id': str,
                            'title': str,
                            'author': str,
                            'cover_url': str
                        }
                    ]
                },
                'error': str,
                'platform': str
            }
        """
        pass

    # ========== 用户相关方法 ==========

    @abstractmethod
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户信息

        Args:
            user_id: 用户ID

        Returns:
            Dict: 标准响应格式
            {
                'success': bool,
                'data': {
                    'id': str,
                    'name': str,
                    'avatar': str,
                    'description': str,
                    'follower_count': int,
                    ...
                },
                'error': str,
                'platform': str
            }
        """
        pass

    @abstractmethod
    async def get_user_videos(self, user_id: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """
        获取用户投稿视频

        Args:
            user_id: 用户ID
            limit: 返回数量
            **kwargs: 平台特定参数

        Returns:
            Dict: 标准响应格式
            {
                'success': bool,
                'data': {
                    'videos': [
                        {
                            'id': str,
                            'title': str,
                            'cover_url': str,
                            'publish_time': int
                        }
                    ]
                },
                'error': str,
                'platform': str
            }
        """
        pass

    # ========== 搜索相关方法 ==========

    @abstractmethod
    async def search_videos(self, keyword: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """
        搜索视频

        Args:
            keyword: 搜索关键词
            limit: 返回数量
            **kwargs: 平台特定参数

        Returns:
            Dict: 标准响应格式
            {
                'success': bool,
                'data': {
                    'results': [
                        {
                            'id': str,
                            'title': str,
                            'author': str,
                            'cover_url': str,
                            'duration': int
                        }
                    ]
                },
                'error': str,
                'platform': str
            }
        """
        pass

    @abstractmethod
    async def search_users(self, keyword: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """
        搜索用户

        Args:
            keyword: 搜索关键词
            limit: 返回数量
            **kwargs: 平台特定参数

        Returns:
            Dict: 标准响应格式
            {
                'success': bool,
                'data': {
                    'results': [
                        {
                            'id': str,
                            'name': str,
                            'avatar': str
                        }
                    ]
                },
                'error': str,
                'platform': str
            }
        """
        pass

    # ========== 热门/推荐方法 ==========

    @abstractmethod
    async def get_popular_videos(self, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """
        获取热门视频

        Args:
            limit: 返回数量
            **kwargs: 平台特定参数

        Returns:
            Dict: 标准响应格式
            {
                'success': bool,
                'data': {
                    'videos': [...]
                },
                'error': str,
                'platform': str
            }
        """
        pass

    # ========== 辅助方法 ==========

    def _format_response(
        self, success: bool, data: Any = None, error: str = None
    ) -> Dict[str, Any]:
        """
        格式化标准响应

        Args:
            success: 是否成功
            data: 响应数据
            error: 错误信息

        Returns:
            Dict: 标准响应格式
        """
        response = {"success": success, "platform": self.platform_name}

        if success:
            response["data"] = data
        else:
            response["error"] = error or "未知错误"

        return response

    async def validate_credentials(self) -> Dict[str, Any]:
        """
        验证登录凭据是否有效（可选实现）

        Returns:
            Dict: 标准响应格式
            {
                'success': bool,
                'data': {'valid': bool},
                'error': str,
                'platform': str
            }
        """
        return self._format_response(
            success=True, data={"valid": True, "message": "凭据验证未实现"}
        )
