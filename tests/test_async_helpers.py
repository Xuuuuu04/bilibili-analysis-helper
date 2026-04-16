import asyncio

from src.backend.utils.async_helpers import run_async


async def _sample_coro() -> int:
    await asyncio.sleep(0)
    return 42


def test_run_async_without_running_loop() -> None:
    assert run_async(_sample_coro()) == 42


def test_run_async_with_running_loop() -> None:
    async def _wrapper() -> int:
        return run_async(_sample_coro())

    assert asyncio.run(_wrapper()) == 42
