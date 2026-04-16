"""
AI服务模块
提供AI分析、Agent、提示词等AI相关功能
"""

from src.backend.services.ai.agents.deep_research_agent import DeepResearchAgent
from src.backend.services.ai.ai_helpers import (
    extract_content_from_response,
    extract_tokens_from_response,
    generate_bili_style_pdf,
    parse_analysis_response,
    save_research_report,
    web_search_exa,
)
from src.backend.services.ai.ai_service import AIService
from src.backend.services.ai.prompts import (
    get_article_analysis_prompt,
    get_chat_qa_system_prompt,
    get_deep_research_system_prompt,
    get_mindmap_prompt,
    get_summary_prompt,
    get_user_portrait_prompt,
    get_video_analysis_prompt,
)

__all__ = [
    # Main Service
    "AIService",
    # Agents
    "DeepResearchAgent",
    # Prompts
    "get_deep_research_system_prompt",
    "get_video_analysis_prompt",
    "get_summary_prompt",
    "get_mindmap_prompt",
    "get_chat_qa_system_prompt",
    "get_article_analysis_prompt",
    "get_user_portrait_prompt",
    # Helpers
    "web_search_exa",
    "save_research_report",
    "generate_bili_style_pdf",
    "extract_content_from_response",
    "extract_tokens_from_response",
    "parse_analysis_response",
]
