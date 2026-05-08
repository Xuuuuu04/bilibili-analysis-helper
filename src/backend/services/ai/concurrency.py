import os
import random
import threading
import time
from contextlib import contextmanager

OPENAI_CONCURRENCY = int(os.getenv("OPENAI_CONCURRENCY", "2"))
EXA_CONCURRENCY = int(os.getenv("EXA_CONCURRENCY", "1"))
BILIBILI_FRAMES_CONCURRENCY = int(os.getenv("BILIBILI_FRAMES_CONCURRENCY", "1"))

OPENAI_SEMAPHORE = threading.BoundedSemaphore(value=max(1, OPENAI_CONCURRENCY))
EXA_SEMAPHORE = threading.BoundedSemaphore(value=max(1, EXA_CONCURRENCY))
BILIBILI_FRAMES_SEMAPHORE = threading.BoundedSemaphore(value=max(1, BILIBILI_FRAMES_CONCURRENCY))


@contextmanager
def _semaphore(sema: threading.Semaphore):
    sema.acquire()
    try:
        yield
    finally:
        sema.release()


def _sleep_backoff(attempt: int, base: float = 0.5, cap: float = 10.0):
    delay = min(cap, base * (2**attempt))
    delay = delay * (0.75 + random.random() * 0.5)
    time.sleep(delay)
