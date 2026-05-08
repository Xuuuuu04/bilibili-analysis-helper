from src.backend.services.ai.concurrency import OPENAI_SEMAPHORE, _semaphore, _sleep_backoff
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


def openai_chat_completions_stream(client, *, max_retries: int = 4, **params):
    attempt = 0
    while True:
        try:
            with _semaphore(OPENAI_SEMAPHORE):
                stream = client.chat.completions.create(**params)
        except Exception as e:
            msg = str(e)
            retryable = any(
                x in msg
                for x in ["429", "Rate limit", "timeout", "timed out", "502", "503", "504"]
            )
            if attempt >= max_retries or not retryable:
                raise
            _sleep_backoff(attempt)
            attempt += 1
            continue

        try:
            for chunk in stream:
                yield chunk
        except Exception:
            raise
        return
