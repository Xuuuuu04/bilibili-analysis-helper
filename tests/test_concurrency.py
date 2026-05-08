import threading
from unittest.mock import patch

from src.backend.services.ai.concurrency import (
    BILIBILI_FRAMES_SEMAPHORE,
    EXA_SEMAPHORE,
    OPENAI_SEMAPHORE,
    _semaphore,
    _sleep_backoff,
)


def test_semaphore_acquires_and_releases():
    sema = threading.BoundedSemaphore(value=1)
    assert sema._value == 1

    with _semaphore(sema):
        assert sema._value == 0

    assert sema._value == 1


def test_sleep_backoff_returns_within_range():
    with patch("src.backend.services.ai.concurrency.time.sleep") as mock_sleep:
        _sleep_backoff(attempt=0, base=0.5, cap=10.0)
        call_args = mock_sleep.call_args[0][0]
        assert 0.375 <= call_args <= 0.75

    with patch("src.backend.services.ai.concurrency.time.sleep") as mock_sleep:
        _sleep_backoff(attempt=1, base=0.5, cap=10.0)
        call_args = mock_sleep.call_args[0][0]
        assert 0.75 <= call_args <= 1.5


def test_semaphore_values():
    assert isinstance(OPENAI_SEMAPHORE, threading.BoundedSemaphore)
    assert isinstance(EXA_SEMAPHORE, threading.BoundedSemaphore)
    assert isinstance(BILIBILI_FRAMES_SEMAPHORE, threading.BoundedSemaphore)
