import time
from unittest.mock import patch

from src.backend.services.ai.cache import TTLCache


def test_get_set_basic():
    cache = TTLCache()
    cache.set("key1", "value1", ttl_seconds=60)
    assert cache.get("key1") == "value1"


def test_get_missing_key():
    cache = TTLCache()
    assert cache.get("nonexistent") is None


def test_get_expired():
    cache = TTLCache()
    cache.set("key1", "value1", ttl_seconds=1)

    with patch("src.backend.services.ai.cache.time.time") as mock_time:
        mock_time.return_value = 100.0
        cache.set("key1", "value1", ttl_seconds=1)

    with patch("src.backend.services.ai.cache.time.time") as mock_time:
        mock_time.return_value = 200.0
        assert cache.get("key1") is None


def test_set_no_ttl():
    cache = TTLCache()
    cache.set("key1", "value1", ttl_seconds=0)

    with patch("src.backend.services.ai.cache.time.time") as mock_time:
        mock_time.return_value = 9999999.0
        assert cache.get("key1") == "value1"


def test_overwrite():
    cache = TTLCache()
    cache.set("key1", "old_value", ttl_seconds=60)
    cache.set("key1", "new_value", ttl_seconds=60)
    assert cache.get("key1") == "new_value"
