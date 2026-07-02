from __future__ import annotations

from pathlib import Path

from ppt_backend.exporters.pptx_components import build_component_renderer_registry
from ppt_backend.exporters.pptx_exporter import PptxExporter
from ppt_backend.repos.presentation_repo import FilePresentationRepository
from ppt_backend.services.presentation_service import PresentationService
from ppt_backend.services.rendering.compiler import RenderCompiler
from ppt_backend.services.rendering.registry import (
    build_layout_registry,
    build_slide_composer_registry,
)


def sample_full_dsl() -> dict:
    return {
        "title": "Slideon Validation Deck",
        "audience": "Course reviewers",
        "tone": "Professional and concise",
        "theme": "paper_light",
        "slides": [
            {
                "id": "s_cover",
                "intent": "cover",
                "section": "Opening",
                "title": "Slideon Test Deck",
                "subtitle": "Layered test validation",
                "tagline": "AI outline generation with RAG grounding",
                "highlights": ["Fast outline generation", "Knowledge-based content", "PPTX export"],
                "notes": ["Introduce the test scope"],
            },
            {
                "id": "s_agenda",
                "intent": "agenda",
                "section": "Opening",
                "title": "Agenda",
                "items": ["Backend/API", "AI generation", "RAG", "Rendering/export"],
                "notes": ["Show logical hierarchy"],
            },
            {
                "id": "s_text",
                "intent": "text",
                "section": "Backend",
                "title": "Backend API Capability",
                "paragraphs": ["FastAPI exposes generation, RAG, evaluation, and export endpoints."],
                "bullets": ["RESTful schema", "Pydantic validation", "Error handling"],
                "notes": ["Verify content generation"],
            },
            {
                "id": "s_timeline",
                "intent": "timeline",
                "section": "Plan",
                "title": "Implementation Timeline",
                "events": [
                    {"label": "Planning", "date": "Mar", "detail": "Requirements and work baseline"},
                    {"label": "Development", "date": "Apr-May", "detail": "Core modules"},
                    {"label": "Testing", "date": "Jun", "detail": "Validation report"},
                ],
                "notes": [],
            },
            {
                "id": "s_kpi",
                "intent": "kpi",
                "section": "Quality",
                "title": "Quality Gates",
                "items": [
                    {"label": "Accuracy", "value": "4.2", "unit": "/5"},
                    {"label": "Speed", "value": "48", "unit": "s"},
                ],
                "notes": [],
            },
            {
                "id": "s_comparison",
                "intent": "comparison",
                "section": "Comparison",
                "title": "Pure LLM vs RAG",
                "left": {"title": "Pure LLM", "bullets": ["Fast", "Weak citations"]},
                "right": {"title": "RAG", "bullets": ["Grounded", "Traceable sources"]},
                "notes": [],
            },
            {
                "id": "s_swot",
                "intent": "swot",
                "section": "Analysis",
                "title": "System SWOT",
                "swot": {
                    "strengths": ["Structured DSL"],
                    "weaknesses": ["External API dependency"],
                    "opportunities": ["Domain knowledge bases"],
                    "threats": ["Hallucination risk"],
                },
                "notes": [],
            },
            {
                "id": "s_roadmap",
                "intent": "roadmap",
                "section": "Plan",
                "title": "Roadmap",
                "phases": [
                    {"name": "MVP", "timeframe": "Phase 1", "deliverables": ["Outline generation"]},
                    {"name": "Validation", "timeframe": "Phase 2", "deliverables": ["Test report"]},
                ],
                "notes": [],
            },
            {
                "id": "s_process",
                "intent": "process_flow",
                "section": "Flow",
                "title": "Generation Flow",
                "steps": [
                    {"name": "Input", "detail": "Topic or document"},
                    {"name": "DSL", "detail": "AI structured output"},
                    {"name": "PPTX", "detail": "Rendered export"},
                ],
                "notes": [],
            },
            {
                "id": "s_chart",
                "intent": "chart",
                "section": "Metrics",
                "title": "Metric Trend",
                "chart": {
                    "chartType": "bar",
                    "labels": ["Accuracy", "Coherence", "Citation"],
                    "series": [{"name": "Score", "values": [4.2, 4.1, 3.8]}],
                },
                "notes": [],
            },
            {
                "id": "s_columns",
                "intent": "multi_column",
                "section": "Frontend",
                "title": "Frontend Panels",
                "columns": [
                    {"title": "Editor", "bullets": ["Outline", "Preview"]},
                    {"title": "Knowledge Base", "bullets": ["Upload", "Search"]},
                ],
                "notes": [],
            },
            {
                "id": "s_arch",
                "intent": "architecture",
                "section": "Architecture",
                "title": "Layered Architecture",
                "layers": [
                    {"name": "Frontend", "items": ["Vue 3", "Pinia"]},
                    {"name": "Backend", "items": ["FastAPI", "Pydantic"]},
                    {"name": "Data", "items": ["PostgreSQL", "Milvus"]},
                ],
                "notes": [],
            },
            {
                "id": "s_quote",
                "intent": "quote",
                "section": "Closing",
                "title": "Takeaway",
                "quote": "Reliable generation requires both structure and evidence.",
                "author": "Slideon Team",
                "notes": [],
            },
            {
                "id": "s_divider",
                "intent": "divider",
                "section": "Appendix",
                "title": "Appendix",
                "subtitle": "Detailed evidence",
                "notes": [],
            },
            {
                "id": "s_team",
                "intent": "team",
                "section": "Team",
                "title": "Team",
                "members": [
                    {"name": "Team Lead", "role": "Architecture", "highlights": ["Requirements", "QA"]},
                    {"name": "Engineer", "role": "Backend", "highlights": ["API", "Export"]},
                ],
                "notes": [],
            },
        ],
    }


def make_presentation_service(base_dir: Path) -> PresentationService:
    return PresentationService(
        repo=FilePresentationRepository(base_dir),
        ai=object(),
        compiler=RenderCompiler(build_slide_composer_registry(), build_layout_registry()),
        exporter=PptxExporter(build_component_renderer_registry()),
        rag=None,
    )
