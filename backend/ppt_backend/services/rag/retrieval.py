from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .content_fetcher import ContentFetcher
from .web_search import WebSearchService

if TYPE_CHECKING:
    from .embedding import EmbeddingService
    from .milvus_client import MilvusStore


class HybridRetriever:
    def __init__(
        self,
        store: MilvusStore,
        embedding: EmbeddingService,
        web_search: WebSearchService,
        top_k: int = 5,
        web_ratio: float = 0.4,
        fetcher: Optional[ContentFetcher] = None,
    ):
        self._store = store
        self._embedding = embedding
        self._web = web_search
        self._top_k = top_k
        self._web_ratio = web_ratio
        self._fetcher = fetcher or ContentFetcher()

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        enable_web: bool = True,
        enable_local: bool = True,
        source_filter: Optional[str] = None,
        deep_fetch: bool = True,
        deep_fetch_count: int = 3,
    ) -> Dict[str, Any]:
        k = top_k or self._top_k
        web_results: List[Dict[str, Any]] = []
        local_results: List[Dict[str, Any]] = []

        if enable_web:
            snippets = self._web.search(query, max_results=k)
            if deep_fetch and snippets:
                web_results = self._deep_fetch(snippets, max_fetch=deep_fetch_count)
            else:
                web_results = snippets

        if enable_local:
            try:
                query_emb = self._embedding.embed_query(query)
                local_results = self._store.hybrid_search(
                    query_embedding=query_emb,
                    query_text=query,
                    top_k=k,
                    source_filter=source_filter,
                )
            except Exception:
                local_results = []

        fused = self._rrf_fuse(web_results, local_results, k)
        return {
            "query": query,
            "web_results": web_results,
            "local_results": local_results,
            "fused_results": fused,
        }

    def retrieve_context(
        self,
        query: str,
        top_k: Optional[int] = None,
        enable_web: bool = True,
        enable_local: bool = True,
        deep_fetch: bool = True,
    ) -> str:
        result = self.retrieve(
            query, top_k,
            enable_web=enable_web,
            enable_local=enable_local,
            deep_fetch=deep_fetch,
        )
        parts = []
        for i, item in enumerate(result["fused_results"]):
            source = item.get("source", "unknown")
            text = item.get("text") or item.get("snippet", "")
            if not text:
                continue
            head = text[:3000] if len(text) > 3000 else text
            parts.append(f"[来源 {i + 1} - {source}]\n{head}")
        return "\n\n---\n\n".join(parts)

    def _deep_fetch(
        self,
        snippets: List[Dict[str, Any]],
        max_fetch: int = 3,
    ) -> List[Dict[str, Any]]:
        results = []
        for i, snip in enumerate(snippets):
            url = snip.get("url", "")
            if i < max_fetch and url:
                content = self._fetcher.fetch(url)
                if content and len(content) > 200:
                    results.append({
                        "title": snip.get("title", ""),
                        "url": url,
                        "text": content,
                        "snippet": snip.get("snippet", ""),
                        "source": f"web:{snip.get('title', url)[:60]}",
                    })
                    time.sleep(0.3)
                    continue
            results.append({
                "title": snip.get("title", ""),
                "url": url,
                "text": snip.get("snippet", ""),
                "snippet": snip.get("snippet", ""),
                "source": "web",
            })
        return results

    def _rrf_fuse(
        self,
        web_results: List[Dict[str, Any]],
        local_results: List[Dict[str, Any]],
        top_k: int,
        rrf_k: int = 60,
    ) -> List[Dict[str, Any]]:
        scores: Dict[int, float] = {}
        items: Dict[int, Dict[str, Any]] = {}

        for rank, item in enumerate(local_results):
            key = -hash(item.get("text", ""))
            rrf_score = 1.0 / (rrf_k + rank + 1)
            scores[key] = scores.get(key, 0) + rrf_score
            items[key] = item

        for rank, item in enumerate(web_results):
            key = hash(item.get("url", item.get("text", "")))
            rrf_score = 1.0 / (rrf_k + rank + 1) * self._web_ratio
            scores[key] = scores.get(key, 0) + rrf_score
            if key not in items:
                items[key] = item

        sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [items[key] for key, _ in sorted_items[:top_k]]
