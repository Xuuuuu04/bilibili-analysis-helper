import pytest

from src.backend.utils.retry import retry_sync


def test_retry_sync_success_after_retries() -> None:
    state = {"attempt": 0}

    def fn() -> str:
        state["attempt"] += 1
        if state["attempt"] < 3:
            raise RuntimeError("transient")
        return "ok"

    assert retry_sync(fn, retries=3, base_delay=0) == "ok"
    assert state["attempt"] == 3


def test_retry_sync_stops_on_non_retryable() -> None:
    state = {"attempt": 0}

    def fn() -> str:
        state["attempt"] += 1
        raise ValueError("fatal")

    with pytest.raises(ValueError):
        retry_sync(fn, retries=3, base_delay=0, should_retry=lambda exc: "timeout" in str(exc))
    assert state["attempt"] == 1
