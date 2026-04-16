"""
配置管理器模块

提供统一的配置管理、验证和持久化功能
"""

from threading import Lock
from typing import Any, Callable, Dict

from src.backend.utils.env_store import rewrite_env_with_filter, upsert_env_values
from src.backend.utils.logger import get_logger
from src.backend.utils.project_paths import env_file_path
from src.config import Config

logger = get_logger(__name__)


class ConfigManager:
    """
    配置管理器

    提供配置的读取、更新、验证和持久化功能
    """

    def __init__(self):
        """初始化配置管理器"""
        self._lock = Lock()
        self._watchers: Dict[str, list] = {}  # 配置变更监听器

        self._env_file = env_file_path()

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键（支持点号分隔的嵌套键，如 'openai.model'）
            default: 默认值

        Returns:
            配置值
        """
        # 从 Config 类获取
        value = getattr(Config, key.upper(), default)
        return value

    def set(self, key: str, value: Any, persist: bool = False) -> bool:
        """
        设置配置值

        Args:
            key: 配置键
            value: 配置值
            persist: 是否持久化到 .env 文件

        Returns:
            是否设置成功
        """
        with self._lock:
            try:
                # 更新 Config 对象
                setattr(Config, key.upper(), value)

                logger.info(f"配置已更新: {key} = {'***' if self._is_sensitive(key) else value}")

                # 触发监听器
                self._notify_watchers(key, value)

                # 持久化到 .env 文件
                if persist:
                    self._persist_to_env(key, value)

                return True
            except Exception as e:
                logger.error(f"设置配置失败: {key} = {value}, 错误: {str(e)}")
                return False

    def update_bilibili_credentials(self, credentials: Dict[str, str]) -> bool:
        """
        更新B站凭据并同步到所有服务

        Args:
            credentials: 凭据字典
                - SESSDATA: SESSDATA
                - BILI_JCT: bili_jct
                - BUVID3: buvid3
                - DEDEUSERID: DedeUserID

        Returns:
            是否更新成功
        """
        with self._lock:
            try:
                # 更新 Config
                Config.BILIBILI_SESSDATA = credentials.get("SESSDATA", "")
                Config.BILIBILI_BILI_JCT = credentials.get("BILI_JCT", "")
                Config.BILIBILI_BUVID3 = credentials.get("BUVID3", "")
                Config.BILIBILI_DEDEUSERID = credentials.get("DEDEUSERID", "")

                logger.info("B站凭据已更新到内存")

                # 持久化到 .env 文件
                self._persist_bilibili_credentials(credentials)

                # 触发凭据变更事件
                self._notify_watchers("bilibili_credentials", credentials)

                return True
            except Exception as e:
                logger.error(f"更新B站凭据失败: {str(e)}")
                return False

    def watch(self, key: str, callback: Callable[[Any], None]):
        """
        监听配置变更

        Args:
            key: 配置键
            callback: 回调函数
        """
        if key not in self._watchers:
            self._watchers[key] = []
        self._watchers[key].append(callback)
        logger.debug(f"注册配置监听器: {key}")

    def _notify_watchers(self, key: str, value: Any):
        """
        通知配置变更监听器

        Args:
            key: 配置键
            value: 新值
        """
        if key in self._watchers:
            for callback in self._watchers[key]:
                try:
                    callback(value)
                except Exception as e:
                    logger.error(f"配置监听器回调失败: {key}, 错误: {str(e)}")

    def _persist_to_env(self, key: str, value: str):
        """
        持久化配置到 .env 文件

        Args:
            key: 配置键
            value: 配置值
        """
        try:
            env_key = key.upper()
            upsert_env_values({env_key: str(value)}, self._env_file)

            logger.debug(f"配置已持久化到 .env: {env_key}")
        except Exception as e:
            logger.error(f"持久化配置失败: {key}, 错误: {str(e)}")

    def _persist_bilibili_credentials(self, credentials: Dict[str, str]):
        """
        持久化B站凭据到 .env 文件

        Args:
            credentials: 凭据字典
        """
        try:
            updates = {
                "BILIBILI_SESSDATA": credentials.get("SESSDATA", ""),
                "BILIBILI_BILI_JCT": credentials.get("BILI_JCT", ""),
                "BILIBILI_BUVID3": credentials.get("BUVID3", ""),
                "BILIBILI_DEDEUSERID": credentials.get("DEDEUSERID", ""),
            }
            rewrite_env_with_filter(
                keep_if=lambda key: not key.startswith("OPENAI_"),
                updates=updates,
                path=self._env_file,
            )

            logger.info("B站凭据已持久化到 .env 文件")
        except Exception as e:
            logger.error(f"持久化B站凭据失败: {str(e)}")

    def _is_sensitive(self, key: str) -> bool:
        """
        判断配置是否敏感

        Args:
            key: 配置键

        Returns:
            是否敏感
        """
        sensitive_keys = ["key", "token", "password", "secret", "cookie", "sessdata"]
        return any(sk in key.lower() for sk in sensitive_keys)

    def validate_required(self) -> bool:
        """
        验证必需配置是否存在

        Returns:
            是否全部配置
        """
        required_configs = {"OPENAI_API_KEY": "AI服务密钥", "OPENAI_MODEL": "主分析模型"}

        missing = []
        for key, desc in required_configs.items():
            if not getattr(Config, key, None):
                missing.append(desc)

        if missing:
            logger.error(f"缺少必需配置: {', '.join(missing)}")
            return False

        logger.info("所有必需配置已就绪")
        return True

    def get_config_summary(self) -> Dict[str, Any]:
        """
        获取配置摘要（脱敏）

        Returns:
            配置摘要字典
        """
        return {
            "ai_model": Config.OPENAI_MODEL,
            "qa_model": Config.QA_MODEL,
            "research_model": Config.DEEP_RESEARCH_MODEL,
            "api_base": Config.OPENAI_API_BASE,
            "api_key_configured": bool(Config.OPENAI_API_KEY),
            "bilibili_logged_in": bool(Config.BILIBILI_SESSDATA),
            "host": Config.HOST,
            "port": Config.PORT,
        }


# 全局单例
config_manager = ConfigManager()
