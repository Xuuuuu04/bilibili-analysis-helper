from typing import Dict, Generator

from openai import OpenAI

from src.backend.services.ai.prompts import get_article_analysis_prompt
from src.backend.utils.logger import get_logger
from src.backend.utils.retry import retry_sync

logger = get_logger(__name__)


class ArticleAnalysisService:
    def __init__(self, client: OpenAI, qa_model: str):
        self.client = client
        self.qa_model = qa_model

    @staticmethod
    def _is_retryable_error(exc: Exception) -> bool:
        msg = str(exc).lower()
        return any(
            token in msg
            for token in ("timeout", "timed out", "connection", "429", "502", "503", "504")
        )

    def _create_completion(self, **kwargs):
        return retry_sync(
            lambda: self.client.chat.completions.create(**kwargs),
            retries=2,
            should_retry=self._is_retryable_error,
        )

    def generate_article_analysis_stream(
        self, article_info: Dict, content: str
    ) -> Generator[Dict, None, None]:
        try:
            if article_info is None:
                article_info = {}
            prompt = get_article_analysis_prompt(article_info, content)

            messages = [
                {
                    "role": "system",
                    "content": "你是一位资深的B站专栏分析专家，擅长逻辑分析与深度总结。",
                },
                {"role": "user", "content": prompt},
            ]

            stream = self._create_completion(
                model=self.qa_model, messages=messages, temperature=0.3, stream=True
            )

            full_content = ""
            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "content") and delta.content:
                        full_content += delta.content
                        yield {"type": "content", "content": delta.content}

            sections = {
                "summary": full_content,
                "danmaku": "专栏文章暂无弹幕分析",
                "comments": "专栏文章暂无评论分析",
            }
            yield {"type": "final", "parsed": sections, "full_analysis": full_content}

        except Exception as e:
            yield {"type": "error", "error": str(e)}
