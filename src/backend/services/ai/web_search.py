from typing import Dict

import requests

from src.backend.services.ai.cache import EXA_CACHE
from src.backend.services.ai.concurrency import EXA_SEMAPHORE, _semaphore, _sleep_backoff
from src.backend.utils.logger import get_logger
from src.config import Config

logger = get_logger(__name__)


def web_search_exa(query: str) -> Dict:
    try:
        api_key = Config.EXA_API_KEY
        if not api_key:
            return {"success": False, "error": "未配置 Exa API Key"}

        cached = EXA_CACHE.get(("exa_search", query))
        if cached is not None:
            return {"success": True, "data": cached}

        headers = {"x-api-key": api_key, "Content-Type": "application/json"}
        payload = {"query": query, "useAutoprompt": True, "numResults": 5, "type": "neural"}

        logger.info(f"[工具] Exa 网络搜索: {query}")
        with _semaphore(EXA_SEMAPHORE):
            for attempt in range(4):
                try:
                    response = requests.post(
                        "https://api.exa.ai/search",
                        json=payload,
                        headers=headers,
                        timeout=(5, 20),
                    )
                    try:
                        res_data = response.json()
                    except Exception:
                        res_data = {}

                    if response.status_code == 200 and "results" in res_data:
                        results = []
                        for item in res_data["results"]:
                            results.append(
                                {
                                    "title": item.get("title", "无标题"),
                                    "url": item.get("url", ""),
                                    "published_date": item.get("publishedDate", "未知"),
                                }
                            )
                        EXA_CACHE.set(("exa_search", query), results, ttl_seconds=600)
                        return {"success": True, "data": results}

                    retryable = response.status_code in (408, 429, 500, 502, 503, 504)
                    if attempt < 3 and retryable:
                        _sleep_backoff(attempt)
                        continue

                    error = res_data.get("error") if isinstance(res_data, dict) else None
                    return {"success": False, "error": error or f"HTTP {response.status_code}"}
                except (requests.Timeout, requests.ConnectionError) as e:
                    if attempt < 3:
                        _sleep_backoff(attempt)
                        continue
                    raise e
    except Exception as e:
        logger.error(f"Exa 搜索失败: {e}")
        return {"success": False, "error": str(e)}
