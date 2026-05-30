from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse


class ContentFetcher:
    def __init__(self, timeout: int = 15, max_retries: int = 2):
        self._timeout = timeout
        self._max_retries = max_retries
        self._session = None

    def _get_session(self):
        if self._session is None:
            import requests
            self._session = requests.Session()
            self._session.headers.update({
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            })
        return self._session

    def fetch(self, url: str) -> Optional[str]:
        for attempt in range(self._max_retries + 1):
            try:
                resp = self._get_session().get(url, timeout=self._timeout)
                resp.raise_for_status()
                resp.encoding = resp.apparent_encoding or "utf-8"
                return self._extract_text(resp.text, url)
            except Exception:
                if attempt < self._max_retries:
                    time.sleep(1 * (attempt + 1))
        return None

    def fetch_batch(self, urls: List[str], on_progress=None) -> List[Tuple[str, Optional[str]]]:
        results = []
        for i, url in enumerate(urls):
            content = self.fetch(url)
            results.append((url, content))
            if on_progress:
                on_progress(i + 1, len(urls))
        return results

    def search_and_fetch(
        self,
        query: str,
        max_urls: int = 5,
        region: str = "wt-wt",
    ) -> List[Dict[str, Any]]:
        urls = self._search_urls(query, max_urls, region)
        docs = []
        for url in urls:
            content = self.fetch(url)
            if content and len(content) > 200:
                docs.append({
                    "url": url,
                    "title": self._guess_title(content),
                    "content": content,
                    "query": query,
                })
            time.sleep(0.5)
        return docs

    def _search_urls(self, query: str, max_results: int, region: str) -> List[str]:
        try:
            from ddgs import DDGS
        except ImportError:
            try:
                from duckduckgo_search import DDGS
            except ImportError:
                return []

        urls = []
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(query, region=region, max_results=max_results):
                    href = r.get("href", "")
                    if href and self._is_fetchable(href):
                        urls.append(href)
        except Exception:
            pass
        return urls

    def _is_fetchable(self, url: str) -> bool:
        skip_domains = {
            "youtube.com", "youtu.be", "instagram.com", "facebook.com",
            "twitter.com", "x.com", "tiktok.com", "linkedin.com",
            "apple.com/podcast", "podcasts.apple.com",
        }
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        for sd in skip_domains:
            if sd in domain:
                return False
        return parsed.scheme in ("http", "https") and bool(domain)

    def _extract_text(self, html: str, url: str = "") -> str:
        try:
            import trafilatura
            text = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
            )
            if text and len(text) > 200:
                return self._clean_text(text)
        except Exception:
            pass

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
                tag.decompose()
            body = soup.find("body") or soup
            text = body.get_text(separator="\n")
            return self._clean_text(text)
        except ImportError:
            pass

        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"&[a-z]+;", " ", text)
        return self._clean_text(text)

    def _clean_text(self, text: str) -> str:
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        lines = [l.strip() for l in text.split("\n")]
        lines = [l for l in lines if l and len(l) > 3]
        return "\n".join(lines)

    def _guess_title(self, text: str) -> str:
        lines = text.strip().split("\n")
        for line in lines[:5]:
            line = line.strip()
            if 5 <= len(line) <= 120:
                return line
        return text[:80].strip()
