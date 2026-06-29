from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from .retrieval import HybridRetriever

if TYPE_CHECKING:
    from .embedding import EmbeddingService
    from .milvus_client import MilvusStore


class RAGState(TypedDict):
    topic: str
    context: str
    search_queries: List[str]
    web_results: List[Dict[str, Any]]
    local_results: List[Dict[str, Any]]
    fused_results: List[Dict[str, Any]]
    images: List[Dict[str, Any]]
    enhanced_context: str
    error: Optional[str]


def build_rag_graph(
    retriever: HybridRetriever,
    llm_for_analysis=None,
):
    graph = StateGraph(RAGState)

    async def analyze_query(state: RAGState) -> Dict[str, Any]:
        topic = state.get("topic", "")
        if not topic:
            return {"search_queries": [], "error": "No topic provided"}

        queries = [topic]

        if llm_for_analysis:
            try:
                from langchain_core.prompts import ChatPromptTemplate

                prompt = ChatPromptTemplate.from_messages([
                    ("system",
                     "你是一个搜索查询生成器。根据用户主题，生成3-5个不同的搜索查询字符串。"
                     "每个查询应该从不同角度搜索相关信息。只输出查询列表，每行一个，不要编号或额外文字。"),
                    ("human", "主题: {topic}"),
                ])
                messages = prompt.format_messages(topic=topic)
                resp = llm_for_analysis.invoke(messages)
                content = getattr(resp, "content", "")
                if content:
                    extra = [q.strip() for q in content.strip().split("\n") if q.strip()]
                    queries.extend(extra)
            except Exception:
                pass

        seen = set()
        unique = []
        for q in queries:
            if q not in seen:
                seen.add(q)
                unique.append(q)
        return {"search_queries": unique[:5]}

    async def web_search_node(state: RAGState) -> Dict[str, Any]:
        queries = state.get("search_queries", [])
        all_results = []
        seen_urls = set()
        for q in queries[:3]:
            results = retriever._web.search(q, max_results=5)
            for r in results:
                url = r.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_results.append(r)
        return {"web_results": all_results[:10]}

    async def local_search_node(state: RAGState) -> Dict[str, Any]:
        queries = state.get("search_queries", [])
        try:
            query_emb = retriever._embedding.embed_query(state["topic"])
            local_results = retriever._store.hybrid_search(
                query_embedding=query_emb,
                query_text=state["topic"],
                top_k=8,
            )
        except Exception:
            local_results = []
        return {"local_results": local_results}

    async def fuse_node(state: RAGState) -> Dict[str, Any]:
        web = state.get("web_results", [])
        local = state.get("local_results", [])
        fused = retriever._rrf_fuse(web, local, top_k=8)
        return {"fused_results": fused}

    async def enrich_images(state: RAGState) -> Dict[str, Any]:
        queries = state.get("search_queries", [])
        all_images = []
        for q in queries[:2]:
            imgs = retriever.search_images(q, max_results=3)
            all_images.extend(imgs)
        return {"images": all_images[:6]}

    async def build_context(state: RAGState) -> Dict[str, Any]:
        fused = state.get("fused_results", [])
        parts = []
        for i, item in enumerate(fused):
            source = item.get("source", "unknown")
            text = item.get("text") or item.get("snippet", "")
            if not text:
                continue
            parts.append(f"[来源 {i + 1} - {source}]\n{text}")

        images = state.get("images", [])
        if images:
            parts.append("\n## 相关图片资源")
            for i, img in enumerate(images):
                parts.append(
                    f"[图片 {i + 1}] 标题: {img.get('title', '')}\n"
                    f"URL: {img.get('url', '')}\n"
                    f"来源: {img.get('source_url', '')}"
                )

        context = "\n\n---\n\n".join(parts) if parts else ""
        return {
            "context": context,
            "enhanced_context": context,
        }

    graph.add_node("analyze_query", analyze_query)
    graph.add_node("web_search", web_search_node)
    graph.add_node("local_search", local_search_node)
    graph.add_node("fuse", fuse_node)
    graph.add_node("enrich_images", enrich_images)
    graph.add_node("build_context", build_context)

    graph.set_entry_point("analyze_query")
    graph.add_edge("analyze_query", "web_search")
    graph.add_edge("analyze_query", "local_search")
    graph.add_edge("analyze_query", "enrich_images")
    graph.add_edge("web_search", "fuse")
    graph.add_edge("local_search", "fuse")
    graph.add_edge("fuse", "build_context")
    graph.add_edge("enrich_images", "build_context")
    graph.add_edge("build_context", END)

    return graph.compile()
