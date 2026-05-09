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
    return PresentationService(repo=repo, ai=ai, compiler=compiler, exporter=exporter)

