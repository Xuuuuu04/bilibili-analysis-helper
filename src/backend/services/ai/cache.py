import threading
import time

from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class TTLCache:
    def __init__(self):
        self._lock = threading.Lock()
        self._store = {}

    def get(self, key):
        now = time.time()
        with self._lock:
            item = self._store.get(key)
            if not item:
                return None
            value, expire_at = item
            if expire_at and expire_at < now:
                self._store.pop(key, None)
                return None
            return value

    def set(self, key, value, ttl_seconds: int):
        expire_at = time.time() + ttl_seconds if ttl_seconds else None
        with self._lock:
            self._store[key] = (value, expire_at)


EXA_CACHE = TTLCache()
BILIBILI_CACHE = TTLCache()
