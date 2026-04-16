"""
B站数据源实现

包装现有的 BilibiliService，实现 DataSource 接口。
提供统一的 B站数据访问方式，支持视频、用户、评论、搜索等功能。
"""

import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from src.backend.services.bilibili.bilibili_service import BilibiliService
from src.backend.services.data_sources.base import DataSource
from src.backend.services.data_sources.exceptions import (
    InvalidURLError,
)
from src.backend.utils.bilibili_helpers import extract_article_id, extract_bvid
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class BilibiliSource(DataSource):
    """
    B站数据源实现类

    通过适配器模式包装现有的 BilibiliService，实现标准 DataSource 接口。
    支持所有 B站相关功能：视频、用户、评论、搜索等。

    Attributes:
        platform_name: 平台名称 "bilibili"
        supported_domains: 支持的域名列表
    """

    # 正则表达式模式
    _BVID_PATTERN = re.compile(r"BV[a-zA-Z0-9]{10}")
    _UID_PATTERN = re.compile(r"/(\d+)/?$")  # 匹配URL末尾的数字UID

    def __init__(self, credential=None):
        """
        初始化B站数据源

        Args:
            credential: B站登录凭据（可选）
        """
        self._service = BilibiliService()
        if credential:
            # 设置凭据（通过 BilibiliService 内部机制）
            logger.info("B站数据源已初始化（带凭据）")
        else:
            logger.info("B站数据源已初始化（无凭据）")

    @property
    def platform_name(self) -> str:
        """平台名称"""
        return "bilibili"

    @property
    def supported_domains(self) -> List[str]:
        """支持的域名列表"""
        return ["bilibili.com", "b23.tv", "www.bilibili.com", "m.bilibili.com"]

    # ========== URL 解析方法 ==========

    def is_supported_url(self, url: str) -> bool:
        """
        检查URL是否被支持

        Args:
            url: 待检查的URL

        Returns:
            bool: 支持返回 True
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            for supported_domain in self.supported_domains:
                if supported_domain in domain:
                    return True

            # 检查是否是直接的 BVID
            if self._BVID_PATTERN.fullmatch(url.strip()):
                return True

            return False
        except Exception:
            return False

    async def extract_video_id(self, url: str) -> Optional[str]:
        """
        从URL提取视频ID (BVID)

        Args:
            url: 视频URL

        Returns:
            Optional[str]: BVID，失败返回 None

        Raises:
            InvalidURLError: URL格式不正确
        """
        try:
            bvid = extract_bvid(url)
            if bvid:
                logger.debug(f"从 URL 提取 BVID: {bvid}")
                return bvid

            raise InvalidURLError(url, "无法提取BVID", platform=self.platform_name)
        except Exception as e:
            if isinstance(e, InvalidURLError):
                raise
            raise InvalidURLError(url, str(e), platform=self.platform_name) from e

    async def extract_user_id(self, url: str) -> Optional[str]:
        """
        从URL提取用户ID (UID)

        Args:
            url: 用户主页URL

        Returns:
            Optional[str]: UID，失败返回 None

        支持的URL格式:
            - https://space.bilibili.com/123456
            - https://space.bilibili.com/123456/dynamic
            - 直接UID: 123456
        """
        try:
            # 如果是纯数字，直接作为UID
            if url.strip().isdigit():
                return url.strip()

            # 从URL提取UID
            parsed = urlparse(url)
            path = parsed.path

            # 匹配路径中的数字
            match = self._UID_PATTERN.search(path)
            if match:
                uid = match.group(1)
                logger.debug(f"从 URL 提取 UID: {uid}")
                return uid

            logger.warning(f"无法从URL提取UID: {url}")
            return None
        except Exception as e:
            logger.error(f"提取UID时出错: {str(e)}")
            return None

    async def extract_article_id(self, url: str) -> Optional[str]:
        """
        从URL提取文章ID

        Args:
            url: 文章URL

        Returns:
            Optional[str]: 文章ID，失败返回 None

        支持的URL格式:
            - 专栏: https://www.bilibili.com/read/cv12345
            - Opus: https://www.bilibili.com/opus/123456
        """
        try:
            result = extract_article_id(url)
            if result:
                logger.debug(f"从 URL 提取文章ID: {result}")
                return result

            return None
        except Exception as e:
            logger.error(f"提取文章ID时出错: {str(e)}")
            return None

    # ========== 视频相关方法 ==========

    async def get_video_info(self, video_id: str) -> Dict[str, Any]:
        """
        获取视频基本信息

        Args:
            video_id: BVID

        Returns:
            Dict: 标准响应格式
        """
        try:
            result = await self._service.get_video_info(video_id)

            if result.get("success"):
                # 添加 platform 标识
                result["data"]["platform"] = self.platform_name
                result["platform"] = self.platform_name
                return result
            else:
                return self._format_response(
                    success=False, error=result.get("error", "获取视频信息失败")
                )
        except Exception as e:
            logger.error(f"获取视频信息失败 ({video_id}): {str(e)}")
            return self._format_response(success=False, error=f"获取视频信息失败: {str(e)}")

    async def get_video_subtitles(self, video_id: str, **kwargs) -> Dict[str, Any]:
        """
        获取视频字幕

        Args:
            video_id: BVID
            **kwargs: 平台特定参数

        Returns:
            Dict: 标准响应格式
        """
        try:
            result = await self._service.get_video_subtitles(video_id)

            if result.get("success"):
                result["platform"] = self.platform_name
                return result
            else:
                return self._format_response(
                    success=False, error=result.get("error", "获取字幕失败")
                )
        except Exception as e:
            logger.error(f"获取字幕失败 ({video_id}): {str(e)}")
            return self._format_response(success=False, error=f"获取字幕失败: {str(e)}")

    async def get_video_comments(
        self, video_id: str, max_count: int = 100, sort_by: str = "hot", **kwargs
    ) -> Dict[str, Any]:
        """
        获取视频评论

        Args:
            video_id: BVID
            max_count: 最大评论数
            sort_by: 排序方式 ('hot' 或 'time')
            **kwargs: 平台特定参数

        Returns:
            Dict: 标准响应格式
        """
        try:
            # B站使用 max_pages 而不是 max_count
            # 估算页数: 假设每页20条评论
            max_pages = max(1, (max_count + 19) // 20)

            result = await self._service.get_video_comments(
                video_id, max_pages=max_pages, target_count=max_count
            )

            if result.get("success"):
                result["platform"] = self.platform_name
                return result
            else:
                return self._format_response(
                    success=False, error=result.get("error", "获取评论失败")
                )
        except Exception as e:
            logger.error(f"获取评论失败 ({video_id}): {str(e)}")
            return self._format_response(success=False, error=f"获取评论失败: {str(e)}")

    async def get_video_danmaku(
        self, video_id: str, max_count: int = 1000, **kwargs
    ) -> Dict[str, Any]:
        """
        获取视频弹幕

        Args:
            video_id: BVID
            max_count: 最大弹幕数
            **kwargs: 平台特定参数

        Returns:
            Dict: 标准响应格式
        """
        try:
            result = await self._service.get_video_danmaku(video_id, limit=max_count)

            if result.get("success"):
                result["platform"] = self.platform_name
                return result
            else:
                return self._format_response(
                    success=False, error=result.get("error", "获取弹幕失败")
                )
        except Exception as e:
            logger.error(f"获取弹幕失败 ({video_id}): {str(e)}")
            return self._format_response(success=False, error=f"获取弹幕失败: {str(e)}")

    async def get_video_tags(self, video_id: str) -> Dict[str, Any]:
        """
        获取视频标签

        Args:
            video_id: BVID

        Returns:
            Dict: 标准响应格式
        """
        try:
            result = await self._service.get_video_tags(video_id)

            if result.get("success"):
                result["platform"] = self.platform_name
                return result
            else:
                return self._format_response(
                    success=False, error=result.get("error", "获取标签失败")
                )
        except Exception as e:
            logger.error(f"获取标签失败 ({video_id}): {str(e)}")
            return self._format_response(success=False, error=f"获取标签失败: {str(e)}")

    async def get_related_videos(self, video_id: str, **kwargs) -> Dict[str, Any]:
        """
        获取相关推荐视频

        Args:
            video_id: BVID
            **kwargs: 平台特定参数

        Returns:
            Dict: 标准响应格式
        """
        try:
            result = await self._service.get_related_videos(video_id)

            if result.get("success"):
                result["platform"] = self.platform_name
                return result
            else:
                return self._format_response(
                    success=False, error=result.get("error", "获取相关视频失败")
                )
        except Exception as e:
            logger.error(f"获取相关视频失败 ({video_id}): {str(e)}")
            return self._format_response(success=False, error=f"获取相关视频失败: {str(e)}")

    # ========== 用户相关方法 ==========

    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户信息

        Args:
            user_id: UID

        Returns:
            Dict: 标准响应格式
        """
        try:
            uid = int(user_id)
            result = await self._service.get_user_info(uid)

            if result.get("success"):
                result["platform"] = self.platform_name
                return result
            else:
                return self._format_response(
                    success=False, error=result.get("error", "获取用户信息失败")
                )
        except ValueError:
            return self._format_response(success=False, error=f"无效的用户ID: {user_id}")
        except Exception as e:
            logger.error(f"获取用户信息失败 ({user_id}): {str(e)}")
            return self._format_response(success=False, error=f"获取用户信息失败: {str(e)}")

    async def get_user_videos(self, user_id: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """
        获取用户投稿视频

        Args:
            user_id: UID
            limit: 返回数量
            **kwargs: 平台特定参数

        Returns:
            Dict: 标准响应格式
        """
        try:
            uid = int(user_id)
            result = await self._service.get_user_recent_videos(uid, limit=limit)

            if result.get("success"):
                result["platform"] = self.platform_name
                return result
            else:
                return self._format_response(
                    success=False, error=result.get("error", "获取用户视频失败")
                )
        except ValueError:
            return self._format_response(success=False, error=f"无效的用户ID: {user_id}")
        except Exception as e:
            logger.error(f"获取用户视频失败 ({user_id}): {str(e)}")
            return self._format_response(success=False, error=f"获取用户视频失败: {str(e)}")

    # ========== 搜索相关方法 ==========

    async def search_videos(self, keyword: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """
        搜索视频

        Args:
            keyword: 搜索关键词
            limit: 返回数量
            **kwargs: 平台特定参数

        Returns:
            Dict: 标准响应格式
        """
        try:
            result = await self._service.search_videos(keyword, limit=limit)

            if result.get("success"):
                result["platform"] = self.platform_name
                return result
            else:
                return self._format_response(
                    success=False, error=result.get("error", "搜索视频失败")
                )
        except Exception as e:
            logger.error(f"搜索视频失败 ({keyword}): {str(e)}")
            return self._format_response(success=False, error=f"搜索视频失败: {str(e)}")

    async def search_users(self, keyword: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """
        搜索用户

        Args:
            keyword: 搜索关键词
            limit: 返回数量
            **kwargs: 平台特定参数

        Returns:
            Dict: 标准响应格式
        """
        try:
            result = await self._service.search_users(keyword, limit=limit)

            if result.get("success"):
                result["platform"] = self.platform_name
                return result
            else:
                return self._format_response(
                    success=False, error=result.get("error", "搜索用户失败")
                )
        except Exception as e:
            logger.error(f"搜索用户失败 ({keyword}): {str(e)}")
            return self._format_response(success=False, error=f"搜索用户失败: {str(e)}")

    # ========== 热门/推荐方法 ==========

    async def get_popular_videos(self, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """
        获取热门视频

        Args:
            limit: 返回数量
            **kwargs: 平台特定参数

        Returns:
            Dict: 标准响应格式
        """
        try:
            result = await self._service.get_popular_videos()

            if result.get("success"):
                # 限制返回数量
                videos = result.get("data", [])
                if isinstance(videos, list) and len(videos) > limit:
                    videos = videos[:limit]
                    result["data"] = videos

                result["platform"] = self.platform_name
                return result
            else:
                return self._format_response(
                    success=False, error=result.get("error", "获取热门视频失败")
                )
        except Exception as e:
            logger.error(f"获取热门视频失败: {str(e)}")
            return self._format_response(success=False, error=f"获取热门视频失败: {str(e)}")

    # ========== B站特有方法扩展 ==========

    async def get_article_content(self, article_id: int) -> Dict[str, Any]:
        """
        获取专栏文章内容（B站特有）

        Args:
            article_id: 专栏CV号

        Returns:
            Dict: 标准响应格式
        """
        try:
            result = await self._service.get_article_content(article_id)

            if result.get("success"):
                result["platform"] = self.platform_name
                return result
            else:
                return self._format_response(
                    success=False, error=result.get("error", "获取专栏文章失败")
                )
        except Exception as e:
            logger.error(f"获取专栏文章失败 ({article_id}): {str(e)}")
            return self._format_response(success=False, error=f"获取专栏文章失败: {str(e)}")

    async def get_opus_content(self, opus_id: int) -> Dict[str, Any]:
        """
        获取Opus动态内容（B站特有）

        Args:
            opus_id: Opus ID

        Returns:
            Dict: 标准响应格式
        """
        try:
            result = await self._service.get_opus_content(opus_id)

            if result.get("success"):
                result["platform"] = self.platform_name
                return result
            else:
                return self._format_response(
                    success=False, error=result.get("error", "获取Opus动态失败")
                )
        except Exception as e:
            logger.error(f"获取Opus动态失败 ({opus_id}): {str(e)}")
            return self._format_response(success=False, error=f"获取Opus动态失败: {str(e)}")

    async def validate_credentials(self) -> Dict[str, Any]:
        """
        验证登录凭据是否有效

        Returns:
            Dict: 标准响应格式
        """
        try:
            is_valid = await self._service.check_credential_valid()

            return self._format_response(
                success=True,
                data={"valid": is_valid, "message": "凭据有效" if is_valid else "凭据无效或已过期"},
            )
        except Exception as e:
            logger.error(f"验证凭据失败: {str(e)}")
            return self._format_response(
                success=True,  # 不抛出异常，返回数据
                data={"valid": False, "message": f"验证失败: {str(e)}"},
            )
