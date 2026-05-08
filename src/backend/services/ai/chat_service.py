from typing import Dict, Generator, List, Optional

from openai import OpenAI

from src.backend.services.ai.prompts import get_chat_qa_system_prompt, get_context_qa_system_prompt
from src.backend.utils.logger import get_logger
from src.backend.utils.retry import retry_sync

logger = get_logger(__name__)


class ChatService:
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

    def chat_stream(
        self, question: str, context: str, video_info: Dict, history: List[Dict] = None
    ) -> Generator[Dict, None, None]:
        try:
            if video_info is None:
                video_info = {}

            system_prompt = get_chat_qa_system_prompt(video_info, context)
            messages = [{"role": "system", "content": system_prompt}]

            if history:
                messages.extend(history)
            messages.append({"role": "user", "content": question})

            stream = self._create_completion(
                model=self.qa_model, messages=messages, temperature=0.4, stream=True
            )

            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "content") and delta.content:
                        yield {"type": "content", "content": delta.content}

            yield {"type": "done"}

        except Exception as e:
            logger.error(f"QA问答失败: {str(e)}")
            yield {"type": "error", "error": str(e)}

    def context_qa_stream(
        self,
        mode: str,
        question: str,
        context: str,
        meta: Optional[Dict] = None,
        history: Optional[List[Dict]] = None,
    ) -> Generator[Dict, None, None]:
        try:
            meta = meta or {}
            system_prompt = get_context_qa_system_prompt(mode, meta, context)
            messages = [{"role": "system", "content": system_prompt}]

            if history:
                messages.extend(history)
            messages.append({"role": "user", "content": question})

            stream = self._create_completion(
                model=self.qa_model, messages=messages, temperature=0.4, stream=True
            )

            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "content") and delta.content:
                        yield {"type": "content", "content": delta.content}

            yield {"type": "done"}

        except Exception as e:
            logger.error(f"上下文问答失败: {str(e)}")
            yield {"type": "error", "error": str(e)}
