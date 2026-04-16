"""
输入验证工具模块

提供各种输入验证函数，确保数据安全性和完整性
"""

import re
from typing import Any, List
from urllib.parse import urlparse


class ValidationError(Exception):
    """验证错误异常"""

    pass


def validate_string(
    value: Any, field_name: str = "字段", min_length: int = 0, max_length: int = None
) -> str:
    """
    验证字符串输入

    Args:
        value: 待验证的值
        field_name: 字段名称（用于错误消息）
        min_length: 最小长度
        max_length: 最大长度

    Returns:
        验证后的字符串

    Raises:
        ValidationError: 验证失败
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} 必须是字符串类型")

    if max_length and len(value) > max_length:
        raise ValidationError(f"{field_name} 长度不能超过 {max_length} 个字符")

    if min_length and len(value) < min_length:
        raise ValidationError(f"{field_name} 长度不能少于 {min_length} 个字符")

    return value.strip()


def validate_url(value: Any, field_name: str = "URL", allowed_schemes: List[str] = None) -> str:
    """
    验证URL格式

    Args:
        value: 待验证的URL
        field_name: 字段名称
        allowed_schemes: 允许的协议列表（默认：http, https）

    Returns:
        验证后的URL

    Raises:
        ValidationError: 验证失败
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} 必须是字符串类型")

    if allowed_schemes is None:
        allowed_schemes = ["http", "https"]

    try:
        parsed = urlparse(value)
        if not parsed.scheme or not parsed.netloc:
            raise ValidationError(f"{field_name} 格式无效")

        if parsed.scheme.lower() not in allowed_schemes:
            raise ValidationError(f"{field_name} 协议必须是 {', '.join(allowed_schemes)}")

        return value
    except Exception as e:
        raise ValidationError(f"{field_name} 格式无效: {str(e)}") from e


def validate_integer(
    value: Any, field_name: str = "数值", min_value: int = None, max_value: int = None
) -> int:
    """
    验证整数输入

    Args:
        value: 待验证的值
        field_name: 字段名称
        min_value: 最小值
        max_value: 最大值

    Returns:
        验证后的整数

    Raises:
        ValidationError: 验证失败
    """
    if isinstance(value, str):
        if not value.isdigit():
            raise ValidationError(f"{field_name} 必须是整数")
        value = int(value)
    elif not isinstance(value, int):
        raise ValidationError(f"{field_name} 必须是整数类型")

    if min_value is not None and value < min_value:
        raise ValidationError(f"{field_name} 不能小于 {min_value}")

    if max_value is not None and value > max_value:
        raise ValidationError(f"{field_name} 不能大于 {max_value}")

    return value


def validate_bvid(bvid: str) -> str:
    """
    验证B站视频BVID格式

    BVID格式：BV1xx411c7xx（12位，以BV开头，base64编码）

    Args:
        bvid: 待验证的BVID

    Returns:
        验证后的BVID

    Raises:
        ValidationError: 验证失败
    """
    bvid = validate_string(bvid, "BVID", min_length=10, max_length=15)

    # 如果是完整URL，提取BVID
    if bvid.startswith("http"):
        from src.backend.utils.bilibili_helpers import extract_bvid

        bvid = extract_bvid(bvid)
        if not bvid:
            raise ValidationError("无法从URL中提取有效的BVID")

    # 验证BVID格式（简化验证：以BV开头，长度合理）
    if not bvid.startswith("BV"):
        raise ValidationError("BVID 必须以 'BV' 开头")

    if len(bvid) < 10 or len(bvid) > 15:
        raise ValidationError("BVID 长度无效")

    return bvid


def validate_search_keyword(keyword: str) -> str:
    """
    验证搜索关键词

    Args:
        keyword: 待验证的关键词

    Returns:
        验证后的关键词

    Raises:
        ValidationError: 验证失败
    """
    keyword = validate_string(keyword, "搜索关键词", min_length=1, max_length=100)

    # 过滤危险字符
    dangerous_chars = ["\x00", "\n", "\r", "\t"]
    for char in dangerous_chars:
        if char in keyword:
            raise ValidationError("搜索关键词包含非法字符")

    return keyword


def validate_json_data(data: Any, required_fields: List[str] = None) -> dict:
    """
    验证JSON请求数据

    Args:
        data: 待验证的数据
        required_fields: 必需字段列表

    Returns:
        验证后的字典

    Raises:
        ValidationError: 验证失败
    """
    if not isinstance(data, dict):
        raise ValidationError("请求数据必须是JSON对象")

    if required_fields:
        missing_fields = [
            field for field in required_fields if field not in data or not data[field]
        ]
        if missing_fields:
            raise ValidationError(f"缺少必需字段: {', '.join(missing_fields)}")

    return data


def sanitize_markdown(text: str) -> str:
    """
    清理Markdown文本，移除潜在的XSS攻击代码

    Args:
        text: 待清理的文本

    Returns:
        清理后的文本
    """
    if not isinstance(text, str):
        return text

    # 移除 <script> 标签
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.IGNORECASE | re.DOTALL)

    # 移除 on* 事件属性（如 onclick, onerror）
    text = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', "", text, flags=re.IGNORECASE)

    return text


def validate_question_input(question: Any) -> str:
    """
    验证智能问答的用户输入

    Args:
        question: 用户问题

    Returns:
        验证后的问题

    Raises:
        ValidationError: 验证失败
    """
    question = validate_string(question, "问题", min_length=1, max_length=2000)

    # 清理Markdown格式
    question = sanitize_markdown(question)

    return question
