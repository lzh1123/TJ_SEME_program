from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class WebSearchService:
    def __init__(
        self,
        region: str = "wt-wt",
        max_results: int = 10,
        provider: str = "baidu",
        api_key: str = "",
        timeout: int = 20,
    ):
        self._region = region
        self._max_results = max_results
        self._provider = (provider or "baidu").lower()
        self._api_key = api_key
        self._timeout = timeout

    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        limit = max_results or self._max_results
        if self._provider == "baidu":
            return self._baidu_search(query, limit)
        if self._provider in {"duckduckgo", "ddg", "ddgs"}:
            return self._duckduckgo_search(query, limit)
        logger.warning("Unknown web search provider: %s", self._provider)
        return self._fallback_search(query, limit)

    def _baidu_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        if not self._api_key:
            logger.warning("BAIDU_SEARCH_API_KEY is not configured")
            return self._fallback_search(query, limit)

        payload = {
            "messages": [{"role": "user", "content": query}],
            "edition": "standard",
            "search_source": "baidu_search_v2",
            "search_recency_filter": "week",
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

        try:
            resp = requests.post(
                "https://qianfan.baidubce.com/v2/ai_search/web_search",
                headers=headers,
                json=payload,
                timeout=self._timeout,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.exception("Baidu web search failed: %s", exc)
            return self._fallback_search(query, limit)

        results = self._extract_baidu_results(data, limit)
        if results:
            return results

        content = self._extract_baidu_answer(data)
        if content:
            return [{
                "title": f"百度搜索结果：{query}",
                "url": "",
                "snippet": content,
                "text": content,
                "source": "web:baidu",
            }]

        logger.warning("Baidu web search returned no parseable results for query: %s", query)
        return self._fallback_search(query, limit)

    def _extract_baidu_results(self, data: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []

        def walk(value: Any) -> None:
            if isinstance(value, dict):
                title = self._pick_first(value, ("title", "name", "site_name"))
                url = self._pick_first(value, ("url", "link", "href", "web_url"))
                snippet = self._pick_first(
                    value,
                    ("snippet", "summary", "content", "description", "abstract", "text"),
                )
                if title and (url or snippet):
                    candidates.append({
                        "title": str(title),
                        "url": str(url or ""),
                        "snippet": str(snippet or ""),
                        "source": "web:baidu",
                    })
                for nested in value.values():
                    walk(nested)
            elif isinstance(value, list):
                for item in value:
                    walk(item)

        for key in ("search_results", "results", "references", "documents", "web_search_results"):
            if key in data:
                walk(data[key])
        if not candidates:
            walk(data)

        deduped: List[Dict[str, Any]] = []
        seen = set()
        for item in candidates:
            marker = item.get("url") or f"{item.get('title')}::{item.get('snippet')}"
            if marker in seen:
                continue
            seen.add(marker)
            deduped.append(item)
            if len(deduped) >= limit:
                break
        return deduped

    def _extract_baidu_answer(self, data: Dict[str, Any]) -> str:
        parts: List[str] = []
        for choice in data.get("choices", []) if isinstance(data.get("choices"), list) else []:
            if not isinstance(choice, dict):
                continue
            message = choice.get("message")
            if isinstance(message, dict) and message.get("content"):
                parts.append(str(message["content"]))
            elif choice.get("content"):
                parts.append(str(choice["content"]))

        for key in ("answer", "content", "result", "summary"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                parts.append(value.strip())

        return "\n\n".join(dict.fromkeys(parts)).strip()

    def _duckduckgo_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        try:
            from ddgs import DDGS
        except ImportError:
            try:
                from duckduckgo_search import DDGS
            except ImportError:
                return self._fallback_search(query, limit)

        try:
            with DDGS() as ddgs:
                raw = list(ddgs.text(query, region=self._region, max_results=limit))
        except Exception:
            return self._fallback_search(query, limit)

        return [
            {
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", ""),
                "source": "web:duckduckgo",
            }
            for r in raw
        ]

    def _pick_first(self, data: Dict[str, Any], keys: tuple[str, ...]) -> Any:
        for key in keys:
            value = data.get(key)
            if value:
                return value
        return None

    def _fallback_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        return [
            {
                "title": "Search unavailable",
                "url": "",
                "snippet": f"Web search is currently unavailable. Query: {query}",
                "source": "fallback",
            }
        ]
