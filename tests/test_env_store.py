from pathlib import Path

from src.backend.utils.env_store import (
    read_env_pairs,
    rewrite_env_with_filter,
    upsert_env_values,
)


def test_upsert_and_read_env_values(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    upsert_env_values({"A": "1", "B": "2"}, env_path)
    upsert_env_values({"B": "3", "C": "4"}, env_path)

    values = read_env_pairs(env_path)
    assert values == {"A": "1", "B": "3", "C": "4"}


def test_rewrite_env_with_filter(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    upsert_env_values(
        {"OPENAI_API_KEY": "secret", "BILIBILI_SESSDATA": "x", "MODE": "dev"}, env_path
    )

    rewrite_env_with_filter(
        keep_if=lambda key: not key.startswith("OPENAI_"),
        updates={"BILIBILI_SESSDATA": "y"},
        path=env_path,
    )

    values = read_env_pairs(env_path)
    assert values == {"BILIBILI_SESSDATA": "y", "MODE": "dev"}
