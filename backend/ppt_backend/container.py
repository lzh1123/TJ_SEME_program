from __future__ import annotations

from pathlib import Path

from .exporters.pptx_components import build_component_renderer_registry
from .exporters.pptx_exporter import PptxExporter
from .repos.presentation_repo import FilePresentationRepository
from .services.ai.pipeline import AiPipeline
from .services.presentation_service import PresentationService
from .services.rendering.compiler import RenderCompiler
from .services.rendering.registry import build_layout_registry, build_slide_composer_registry
from .settings import settings


def build_presentation_service() -> PresentationService:
    base_dir = Path(settings.data_dir)
    repo = FilePresentationRepository(base_dir=base_dir)
    ai = AiPipeline()
    slide_composers = build_slide_composer_registry()
    layouts = build_layout_registry()
    compiler = RenderCompiler(slide_composers=slide_composers, layouts=layouts)
    component_renderers = build_component_renderer_registry()
    exporter = PptxExporter(component_renderers=component_renderers)
    rag = _build_rag_service() if settings.rag_enabled else None
    return PresentationService(
        repo=repo,
        ai=ai,
        compiler=compiler,
        exporter=exporter,
        rag=rag,
    )


def _build_rag_service() -> "RagService | None":
    # Deferred imports: RAG dependencies (sentence-transformers, pymilvus, etc.)
    # are heavy and only needed when RAG is enabled.
    try:
        from .services.rag.content_fetcher import ContentFetcher
        from .services.rag.embedding import EmbeddingService
        from .services.rag.knowledge_base import KnowledgeBase
        from .services.rag.milvus_client import MilvusStore
        from .services.rag.rag_service import RagService
        from .services.rag.retrieval import HybridRetriever
        from .services.rag.web_search import WebSearchService

        store = MilvusStore(uri=settings.milvus_uri, db_name=settings.milvus_db)
        embedding = EmbeddingService(model_name=settings.embedding_model)
        web_search = WebSearchService(region=settings.web_search_region)
        kb = KnowledgeBase(store=store, embedding=embedding)
        fetcher = ContentFetcher()
        retriever = HybridRetriever(store=store, embedding=embedding, web_search=web_search, fetcher=fetcher)
        return RagService(
            store=store,
            embedding=embedding,
            web_search=web_search,
            kb=kb,
            retriever=retriever,
        )
    except Exception:
        return None
