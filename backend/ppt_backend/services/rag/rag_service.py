from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from langchain_core.prompts import ChatPromptTemplate

from .knowledge_base import KnowledgeBase
from .rag_graph import build_rag_graph
from .retrieval import HybridRetriever
from .web_search import WebSearchService

if TYPE_CHECKING:
    from .embedding import EmbeddingService
    from .milvus_client import MilvusStore


class RagService:
    def __init__(
        self,
        store: MilvusStore,
        embedding: EmbeddingService,
        web_search: WebSearchService,
        kb: KnowledgeBase,
        retriever: HybridRetriever,
    ):
        self._store = store
        self._embedding = embedding
        self._web = web_search
        self._kb = kb
        self._retriever = retriever
        self._graph = None

    def get_graph(self, llm=None):
        if self._graph is None:
            self._graph = build_rag_graph(self._retriever, llm_for_analysis=llm)
        return self._graph

    def search(
        self,
        query: str,
        top_k: int = 5,
        enable_web: bool = True,
        enable_local: bool = True,
        deep_fetch: bool = True,
    ) -> Dict[str, Any]:
        return self._retriever.retrieve(
            query=query,
            top_k=top_k,
            enable_web=enable_web,
            enable_local=enable_local,
            deep_fetch=deep_fetch,
        )

    def retrieve_context(
        self,
        query: str,
        top_k: int = 5,
        enable_web: bool = True,
        enable_local: bool = True,
        deep_fetch: bool = True,
    ) -> str:
        return self._retriever.retrieve_context(
            query=query,
            top_k=top_k,
            enable_web=enable_web,
            enable_local=enable_local,
            deep_fetch=deep_fetch,
        )

    async def enhance_topic(self, topic: str, llm=None) -> Dict[str, Any]:
        graph = self.get_graph(llm=llm)
        result = await graph.ainvoke({"topic": topic})
        return result

    def enhance_prompt(
        self,
        topic: str,
        base_prompt: str = "",
    ) -> str:
        context = self._retriever.retrieve_context(topic, top_k=5)
        if not context:
            return base_prompt or topic

        enhanced = (
            f"## 用户主题\n{topic}\n\n"
            f"## 参考资料（来自知识库和网络搜索）\n{context}\n\n"
        )
        if base_prompt:
            enhanced += f"## 原始提示\n{base_prompt}"
        return enhanced

    def enhance_presentation_generation(
        self,
        topic: str,
        existing_prompt: str = "",
    ) -> str:
        context = self._retriever.retrieve_context(topic, top_k=5)

        if not context:
            return ""

        rag_block = (
            "\n\n## RAG 增强上下文（来自知识库和网络搜索）\n"
            "以下是与主题相关的最新信息和专业知识，请在生成 PPT 内容时充分利用：\n\n"
            f"{context}\n\n"
            "请基于以上参考资料，丰富 PPT 的内容深度和准确度。涉及数据、案例、趋势时优先使用参考资料中的信息。"
        )
        return rag_block

    def enhance_slide_content(
        self,
        slide_title: str,
        slide_intent: str,
        topic: str,
    ) -> str:
        query = f"{topic} {slide_title} {slide_intent}"
        return self._retriever.retrieve_context(query, top_k=3)

    def ingest_document(
        self,
        file_path: Path,
        metadata: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        force: bool = False,
        source_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Ingest a file into the knowledge base with deduplication.

        Args:
            file_path: Path to the temp file on disk.
            source_override: The ORIGINAL user filename. Must be provided to ensure
                           correct source naming and dedup. If not provided, falls
                           back to path.name (temp filename — will break dedup).

        Returns dict with: chunks_inserted, dedup_skipped, action_taken, file_hash.
        """
        return self._kb.ingest_file(
            file_path,
            metadata=metadata,
            progress_callback=progress_callback,
            force=force,
            source_override=source_override,
        )

    def ingest_text(
        self,
        content: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
        force: bool = False,
    ) -> Dict[str, Any]:
        """Ingest text into the knowledge base with deduplication.

        Returns dict with: chunks_inserted, dedup_skipped, action_taken.
        """
        return self._kb.ingest_text(content, source, metadata=metadata, force=force)

    def remove_document(self, source: str) -> int:
        return self._kb.remove_source(source)

    def get_kb_stats(self) -> Dict[str, Any]:
        return self._kb.get_stats()

    def list_sources(self) -> List[Dict[str, Any]]:
        """List all distinct sources in the knowledge base with chunk counts."""
        return self._kb.list_sources()

    def ensure_collection(self, drop_if_exists: bool = False) -> bool:
        return self._kb.ensure_collection(drop_if_exists=drop_if_exists)

    def bootstrap_knowledge_base(
        self,
        max_articles_per_topic: int = 3,
        max_topics: int = 0,
        on_progress=None,
    ):
        from .seed_knowledge import SeedBootstrapper, ContentFetcher

        bootstrapper = SeedBootstrapper(
            kb=self._kb,
            embedding=self._embedding,
            fetcher=ContentFetcher(),
            max_articles_per_topic=max_articles_per_topic,
            max_topics=max_topics,
        )
        if on_progress:
            bootstrapper.on_progress(on_progress)
        return bootstrapper.run()
