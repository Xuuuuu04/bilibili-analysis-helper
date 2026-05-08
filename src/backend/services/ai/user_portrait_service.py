import traceback
from typing import Dict, List, Optional

from openai import OpenAI

from src.backend.services.ai.ai_helpers import (
    extract_content_from_response,
    extract_tokens_from_response,
)
from src.backend.services.ai.prompts import (
    get_mindmap_prompt,
    get_summary_prompt,
    get_user_portrait_prompt,
)
from src.backend.utils.logger import get_logger
from src.backend.utils.retry import retry_sync

logger = get_logger(__name__)


class UserPortraitService:
    def __init__(self, client: OpenAI, model: str, qa_model: str):
        self.client = client
        self.model = model
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

    def generate_summary(self, video_info: Dict, content: str) -> Dict:
        try:
            prompt = get_summary_prompt(video_info, content)

            response = self._create_completion(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的视频内容分析助手，擅长总结视频内容并提取关键信息。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=4000,
            )

            summary_text = extract_content_from_response(response)
            tokens_used = extract_tokens_from_response(response)

            return {"success": True, "data": {"summary": summary_text, "tokens_used": tokens_used}}
        except Exception as e:
            logger.error(f"生成总结失败: {str(e)}")
            traceback.print_exc()
            return {"success": False, "error": f"生成总结失败: {str(e)}"}

    def generate_mindmap(
        self, video_info: Dict, content: str, summary: Optional[str] = None
    ) -> Dict:
        try:
            prompt = get_mindmap_prompt(video_info, content, summary)

            response = self._create_completion(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的思维导图设计师，擅长将复杂内容结构化为清晰的思维导图。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
            )

            mindmap_text = extract_content_from_response(response)
            tokens_used = extract_tokens_from_response(response)

            return {"success": True, "data": {"mindmap": mindmap_text, "tokens_used": tokens_used}}
        except Exception as e:
            logger.error(f"生成思维导图失败: {str(e)}")
            traceback.print_exc()
            return {"success": False, "error": f"生成思维导图失败: {str(e)}"}

    def generate_user_analysis(self, user_info: Dict, recent_videos: List[Dict]) -> Dict:
        try:
            videos_text = "\n".join(
                [
                    f"- {v.get('title', '未知标题')} (播放: {v.get('play', '未知')}, 时长: {v.get('length', '未知')})"
                    for v in recent_videos
                ]
            )
            prompt = get_user_portrait_prompt(user_info, videos_text)

            response = self._create_completion(
                model=self.qa_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=1000,
            )

            content = extract_content_from_response(response)
            tokens = extract_tokens_from_response(response)

            return {"portrait": content, "tokens_used": tokens}
        except Exception as e:
            return {"portrait": f"暂时无法生成UP主画像: {str(e)}", "tokens_used": 0}
