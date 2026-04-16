"""
B站认证管理模块
负责登录凭据的初始化、刷新和验证
"""

from typing import Optional

from bilibili_api import Credential

from src.backend.utils.logger import get_logger
from src.config import Config

logger = get_logger(__name__)


class CredentialManager:
    """
    B站登录凭据管理器

    负责凭据的初始化、刷新和有效性验证
    """

    def __init__(self):
        """初始化凭据管理器"""
        self._credential: Optional[Credential] = None
        self.refresh()

    def refresh(self):
        """
        刷新登录凭据（从Config重新加载）

        通常在登录成功后调用此方法更新内存中的凭据
        """
        self._credential = self._init_credential()
        logger.info(f"B站服务凭据已刷新 (登录状态: {bool(self._credential)})")

    def _init_credential(self) -> Optional[Credential]:
        """
        初始化B站登录凭据

        Returns:
            Credential对象，如果未配置则返回None
        """
        try:
            if all(
                [Config.BILIBILI_SESSDATA, Config.BILIBILI_BILI_JCT, Config.BILIBILI_DEDEUSERID]
            ):
                credential = Credential(
                    sessdata=Config.BILIBILI_SESSDATA,
                    bili_jct=Config.BILIBILI_BILI_JCT,
                    buvid3=Config.BILIBILI_BUVID3 or "",
                    dedeuserid=Config.BILIBILI_DEDEUSERID,
                )
                logger.info("已加载B站登录凭据，将获取完整数据")
                return credential
            else:
                logger.info("未配置B站登录凭据，将获取有限的公开数据")
                return None
        except Exception as e:
            logger.warning(f"初始化B站凭据失败: {e}")
            return None

    async def check_valid(self) -> bool:
        """
        检查凭据是否有效

        Returns:
            True如果凭据有效，False否则
        """
        if not self._credential:
            return False
        try:
            is_valid = await self._credential.check_valid()
            return is_valid
        except Exception as e:
            logger.warning(f"检查凭据有效性失败: {e}")
            return False

    @property
    def credential(self) -> Optional[Credential]:
        """
        获取当前凭据对象

        Returns:
            Credential对象，如果未配置则返回None
        """
        return self._credential

    @property
    def is_logged_in(self) -> bool:
        """
        检查是否已登录

        Returns:
            True如果已配置凭据，False否则
        """
        return self._credential is not None
