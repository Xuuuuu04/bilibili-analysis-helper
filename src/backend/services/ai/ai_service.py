from typing import Dict, Generator

from openai import OpenAI

from src.backend.services.ai.agents.deep_research_agent import DeepResearchAgent
from src.backend.services.ai.article_analysis_service import ArticleAnalysisService
from src.backend.services.ai.chat_service import ChatService
from src.backend.services.ai.user_portrait_service import UserPortraitService
from src.backend.services.ai.video_analysis_service import VideoAnalysisService
from src.backend.utils.logger import get_logger
from src.config import Config

logger = get_logger(__name__)


class AIService:
    def __init__(self):
        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 未配置，无法初始化 AIService")

        self.client = OpenAI(
            api_key=Config.OPENAI_API_KEY, base_url=Config.OPENAI_API_BASE, timeout=180.0
        )
        self.model = Config.OPENAI_MODEL or Config.QA_MODEL
        self.qa_model = Config.QA_MODEL
        self.research_model = Config.DEEP_RESEARCH_MODEL

        self._video_analysis = VideoAnalysisService(self.client, self.model)
        self._chat = ChatService(self.client, self.qa_model)
        self._article_analysis = ArticleAnalysisService(self.client, self.qa_model)
        self._user_portrait = UserPortraitService(self.client, self.model, self.qa_model)

        self._deep_research_agent = DeepResearchAgent(
            self.client, self.research_model, vl_model=self.model
        )

    def deep_research_stream(self, topic: str, bilibili_service) -> Generator[Dict, None, None]:
        return self._deep_research_agent.stream_research(topic, bilibili_service)

    def chat_stream(self, question, context, video_info, history=None):
        return self._chat.chat_stream(question, context, video_info, history)

    def context_qa_stream(self, mode, question, context, meta=None, history=None):
        return self._chat.context_qa_stream(mode, question, context, meta, history)

    def generate_full_analysis(self, video_info, content, video_frames=None, retry_count=0):
        return self._video_analysis.generate_full_analysis(video_info, content, video_frames, retry_count)

    def generate_full_analysis_stream(self, video_info, content, video_frames=None, progress_callback=None, _is_fallback=False):
        return self._video_analysis.generate_full_analysis_stream(video_info, content, video_frames, progress_callback, _is_fallback)

    def generate_summary(self, video_info, content):
        return self._user_portrait.generate_summary(video_info, content)

    def generate_mindmap(self, video_info, content, summary=None):
        return self._user_portrait.generate_mindmap(video_info, content, summary)

    def generate_article_analysis_stream(self, article_info, content):
        return self._article_analysis.generate_article_analysis_stream(article_info, content)

    def generate_user_analysis(self, user_info, recent_videos):
        return self._user_portrait.generate_user_analysis(user_info, recent_videos)
