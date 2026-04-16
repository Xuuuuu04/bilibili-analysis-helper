"""
异步工具函数模块

提供异步转同步的辅助函数，解决循环依赖问题
"""

import asyncio
import threading
from typing import Any, Coroutine


def run_async(coro: Coroutine[Any, Any, Any]) -> Any:
    """
    在同步上下文中运行异步函数

    Args:
        coro: 异步协程对象

    Returns:
        异步函数的返回值

    Note:
        - 专为 Flask 多线程环境设计
        - 使用 asyncio.run() 确保每个线程都有独立的事件循环
        - 自动处理事件循环的创建和清理
        - 线程安全，避免事件循环冲突
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # 当前线程没有事件循环，直接运行
        return asyncio.run(coro)

    # 当前线程已有事件循环，切到新线程避免 RuntimeError
    result: list[Any] = [None]
    exception: list[BaseException | None] = [None]

    def _runner() -> None:
        try:
            result[0] = asyncio.run(coro)
        except BaseException as exc:  # noqa: B036
            exception[0] = exc

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    thread.join()

    if exception[0] is not None:
        raise exception[0]

    return result[0]
