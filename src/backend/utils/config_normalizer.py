"""
配置标准化模块
"""
from typing import Optional


def normalize_openai_api_base(base_url: Optional[str]) -> Optional[str]:
    """
    标准化 OpenAI API Base URL

    Args:
        base_url: 原始 API 地址

    Returns:
        标准化后的 API 地址，如果为空则返回 None
    """
    if not base_url:
        return None
    normalized = base_url.rstrip("/")
    if not normalized.endswith("/v1") and "openai.com" in normalized:
        return normalized + "/v1"
    return normalized
