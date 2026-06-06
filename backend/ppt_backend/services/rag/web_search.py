from __future__ import annotations

from typing import Any, Dict, List, Optional


class WebSearchService:
    def __init__(self, region: str = "wt-wt", max_results: int = 10):
        self._region = region
        self._max_results = max_results

    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        limit = max_results or self._max_results
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

        results = []
        for r in raw:
            results.append({
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", ""),
                "source": "web",
            })
        return results

    def _fallback_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        return [
            {
                "title": "Search unavailable",
                "url": "",
                "snippet": f"Web search is currently unavailable. Query: {query}",
                "source": "fallback",
            }
        ]
