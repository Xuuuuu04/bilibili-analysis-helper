"""
================================================================================
API 工具函数模块 (src/backend/http/api/utils.py)
================================================================================

【架构位置】
位于 HTTP 层的 API 子模块，提供 API 相关的工具函数。

【主要功能】
1. SSE 数据格式转换：将字典转换为 Server-Sent Events 格式

【SSE 格式说明】
Server-Sent Events (SSE) 是一种服务器推送技术，允许服务器
向客户端持续推送数据。

格式：
data: {"type": "content", "content": "Hello"}

\n\n

【使用方式】
for chunk in stream:
    yield sse_data({"type": "progress", "value": chunk})

================================================================================
"""

import json
from typing import Any


def sse_data(payload: dict[str, Any], ensure_ascii: bool = False) -> str:
    """
    将字典转换为 SSE 格式字符串

    Args:
        payload: 要发送的数据字典
        ensure_ascii: 是否确保 ASCII 编码（False 支持中文）

    Returns:
        str: SSE 格式的字符串，如 "data: {...}\n\n"

    示例：
        >>> sse_data({"type": "hello", "msg": "世界"})
        'data: {"type": "hello", "msg": "世界"}\n\n'
    """
    return f"data: {json.dumps(payload, ensure_ascii=ensure_ascii)}\n\n"
