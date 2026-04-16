from __future__ import annotations

import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from threading import Lock
from typing import Optional

from src.backend.utils.project_paths import env_file_path

_ENV_LOCK = Lock()


def read_env_pairs(path: Optional[Path] = None) -> dict[str, str]:
    target = path or env_file_path()
    pairs: dict[str, str] = {}
    if not target.exists():
        return pairs
    with target.open("r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            pairs[key] = value
    return pairs


def write_env_pairs(pairs: dict[str, str], path: Optional[Path] = None) -> None:
    target = path or env_file_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".env.", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            for key, value in pairs.items():
                handle.write(f"{key}={value}\n")
        os.replace(tmp_path, target)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def upsert_env_values(updates: dict[str, str], path: Optional[Path] = None) -> None:
    with _ENV_LOCK:
        merged = read_env_pairs(path)
        merged.update(updates)
        write_env_pairs(merged, path)


def rewrite_env_with_filter(
    keep_if: Callable[[str], bool], updates: Optional[dict[str, str]] = None, path: Optional[Path] = None
) -> None:
    with _ENV_LOCK:
        current = read_env_pairs(path)
        filtered = {k: v for k, v in current.items() if keep_if(k)}
        if updates:
            filtered.update(updates)
        write_env_pairs(filtered, path)
