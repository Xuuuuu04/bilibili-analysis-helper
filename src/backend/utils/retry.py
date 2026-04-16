import time
from collections.abc import Callable
from typing import Optional, TypeVar

T = TypeVar("T")


def retry_sync(
    fn: Callable[[], T],
    *,
    retries: int = 2,
    base_delay: float = 0.4,
    should_retry: Optional[Callable[[Exception], bool]] = None,
) -> T:
    attempt = 0
    while True:
        try:
            return fn()
        except Exception as exc:
            if attempt >= retries:
                raise
            if should_retry and not should_retry(exc):
                raise
            time.sleep(base_delay * (2**attempt))
            attempt += 1
