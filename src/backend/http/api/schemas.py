"""
================================================================================
API 请求/响应模式定义 (src/backend/http/api/schemas.py)
================================================================================

【架构位置】
位于 HTTP 层的 API 子模块，定义所有 API 的请求和响应数据模型。

【设计模式】
- 数据传输对象模式（DTO）：使用 Pydantic BaseModel 定义数据结构
- 类型提示：使用 Literal 限制枚举值
- 默认值工厂：使用 Field(default_factory=...) 避免可变默认值陷阱

【主要功能】
1. 定义所有 API 请求的数据结构
2. 自动验证请求参数
3. 提供 API 文档的数据模型

【模式列表】
- AnalyzeRequest: 视频分析请求（同步）
- AnalyzeStreamRequest: 视频分析请求（流式）
- ChatStreamRequest: 视频对话请求
- QAStreamRequest: 通用问答请求
- SearchRequest: 搜索请求
- ResearchRequest: 深度研究请求
- UserPortraitRequest: 用户画像请求
- SettingsUpdateRequest: 设置更新请求

================================================================================
"""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """视频分析请求（同步模式）"""

    url: str = ""


class AnalyzeStreamRequest(BaseModel):
    """视频分析请求（流式模式）"""

    url: str = ""
    mode: Literal["video", "article"] = "video"  # 限制只能是 video 或 article


class ChatStreamRequest(BaseModel):
    """视频对话请求"""

    question: str = ""
    context: str = ""
    video_info: dict[str, Any] = Field(default_factory=dict)  # 使用工厂避免可变默认值
    history: list[Any] = Field(default_factory=list)


class QAStreamRequest(BaseModel):
    """通用问答请求（支持多种模式）"""

    question: str = ""
    mode: Literal["video", "article", "user", "research"] = "video"
    context: str = ""
    meta: dict[str, Any] = Field(default_factory=dict)
    history: list[Any] = Field(default_factory=list)


class SearchRequest(BaseModel):
    """搜索请求"""

    keyword: str = ""
    mode: Literal["video", "article", "user"] = "video"


class VideoInfoRequest(BaseModel):
    """视频信息请求"""

    url: str = ""


class VideoSubtitleRequest(BaseModel):
    """视频字幕请求"""

    url: str = ""


class LoginStatusRequest(BaseModel):
    """登录状态查询请求"""

    session_id: str = ""


class ResearchRequest(BaseModel):
    """深度研究请求"""

    topic: str = ""


class UserPortraitRequest(BaseModel):
    """用户画像请求"""

    uid: str = ""


class SettingsUpdateRequest(BaseModel):
    """设置更新请求"""

    openai_api_base: Optional[str] = None
    openai_api_key: Optional[str] = None
    model: Optional[str] = None
    qa_model: Optional[str] = None
    deep_research_model: Optional[str] = None
    exa_api_key: Optional[str] = None
    dark_mode: Optional[bool] = None
    enable_research_thinking: Optional[bool] = None
