"""
HTTP客户端管理模块

提供全局的 aiohttp ClientSession 管理，支持连接池复用
"""

import asyncio
from threading import Lock
from typing import Optional

import aiohttp

from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class HTTPClientManager:
    """
    HTTP客户端管理器

    管理全局的 aiohttp ClientSession，支持连接池复用和自动清理
    """

    _instance: Optional["HTTPClientManager"] = None
    _session: Optional[aiohttp.ClientSession] = None
    _lock = Lock()
    _new_lock = Lock()

    def __new__(cls):
        """线程安全的单例模式"""
        with cls._new_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        """初始化HTTP客户端管理器"""
        # Session 使用惰性初始化，在事件循环中首次请求时创建
        pass

    def _initialize_session(self):
        """初始化 ClientSession"""
        # 配置连接池和超时
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        connector = aiohttp.TCPConnector(
            limit=100,  # 最大连接数
            limit_per_host=30,  # 每个主机的最大连接数
            ttl_dns_cache=300,  # DNS缓存时间
            use_dns_cache=True,  # 启用DNS缓存
        )

        self._session = aiohttp.ClientSession(
            timeout=timeout, connector=connector, raise_for_status=False  # 不自动抛出HTTP错误状态
        )

        logger.info("HTTP客户端Session已初始化")

    async def get_session(self) -> aiohttp.ClientSession:
        """
        获取 ClientSession

        Returns:
            aiohttp.ClientSession 实例
        """
        if self._session is None or self._session.closed:
            with self._lock:
                if self._session is None or self._session.closed:
                    self._initialize_session()

        return self._session

    async def close(self):
        """关闭 ClientSession"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("HTTP客户端Session已关闭")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return await self.get_session()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()


# 全局单例
http_client_manager = HTTPClientManager()


async def get_http_session() -> aiohttp.ClientSession:
    """
    获取全局 HTTP Session

    Usage:
        session = await get_http_session()
        async with session.get(url) as resp:
            data = await resp.json()

    Returns:
        aiohttp.ClientSession 实例
    """
    return await http_client_manager.get_session()


async def close_http_session():
    """关闭全局 HTTP Session"""
    await http_client_manager.close()


def run_async_in_thread(coro):
    """
    在同步上下文中运行异步函数（使用新线程）

    与 run_async 不同的是，这个函数总是创建新的事件循环，
    避免阻塞主事件循环

    Args:
        coro: 异步协程对象

    Returns:
        异步函数的返回值
    """
    import threading

    result = [None]
    exception = [None]

    def run_in_new_loop():
        try:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            result[0] = new_loop.run_until_complete(coro)
            new_loop.close()
        except Exception as e:
            exception[0] = e

    thread = threading.Thread(target=run_in_new_loop)
    thread.start()
    thread.join()

    if exception[0]:
        raise exception[0]

    return result[0]
