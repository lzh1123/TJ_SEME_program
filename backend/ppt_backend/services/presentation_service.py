from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from ..domain.ids import new_id
from ..domain.presentation import PresentationBundle, PresentationMeta
from ..domain.render_tree import ComponentPatch, RenderTree
from ..domain.theme import DEFAULT_THEMES, get_theme_tokens
from ..exporters.pptx_exporter import PptxExporter
from ..repos.presentation_repo import PresentationRepository
from ..settings import settings
from .ai.pipeline import AiPipeline
from .rendering.compiler import RenderCompiler
from .rendering.theme_engine import apply_theme_to_tree


class PresentationService:
    def __init__(
        self,
        repo: PresentationRepository,
        ai: AiPipeline,
        compiler: RenderCompiler,
        exporter: PptxExporter,
        rag=None,
    ):
        self._repo = repo
        self._ai = ai
        self._compiler = compiler
        self._exporter = exporter
        self._rag = rag

    def create(self, topic: str, theme: Optional[str] = None, use_rag: bool = True) -> PresentationBundle:
        presentation_id = new_id("pres")
        rag_context = ""
        if use_rag and self._rag:
            rag_context = self._rag.retrieve_context(topic, top_k=8)
        dsl, ai_debug = self._ai.generate_dsl_with_debug(
            topic=topic, theme=theme, rag_context=rag_context
        )
        theme_tokens = get_theme_tokens(dsl.theme)
        tree = self._compiler.compile(presentation_id, dsl, theme_tokens)
        tree = apply_theme_to_tree(tree, theme_tokens)
        meta = PresentationMeta(id=presentation_id, topic=topic)
        meta.extra = {"ai": ai_debug}
        bundle = PresentationBundle(meta=meta, dsl=dsl, renderTree=tree)
        self._repo.save(bundle)
        return bundle

    def generate_outline(self, topic: str, theme: Optional[str] = None, use_rag: bool = True) -> dict:
        rag_context = ""
        if use_rag and self._rag:
            rag_context = self._rag.retrieve_context(topic, top_k=8)
        dsl = self._ai.generate_dsl(topic=topic, theme=theme, rag_context=rag_context)
        data = dsl.model_dump(by_alias=True)
        slides = data.get("slides") or []
        if isinstance(slides, list):
            for s in slides:
                if isinstance(s, dict):
                    s.pop("id", None)
        data["slides"] = slides
        return data

    def create_from_outline(self, topic: str, outline: dict, theme: Optional[str] = None) -> PresentationBundle:
        presentation_id = new_id("pres")
        hydrated = self._hydrate_outline(outline, topic=topic, theme=theme)
        theme_tokens = get_theme_tokens(hydrated.theme)
        tree = self._compiler.compile(presentation_id, hydrated, theme_tokens)
        tree = apply_theme_to_tree(tree, theme_tokens)
        meta = PresentationMeta(id=presentation_id, topic=topic)
        bundle = PresentationBundle(meta=meta, dsl=hydrated, renderTree=tree)
        self._repo.save(bundle)
        return bundle

    def _hydrate_outline(self, outline: dict, *, topic: str, theme: Optional[str]) -> "PresentationDSL":
        def as_str_list(v):
            if v is None:
                return []
            if isinstance(v, str):
                t = v.strip()
                return [t] if t else []
            if isinstance(v, list):
                out = []
                for it in v:
                    if it is None:
                        continue
                    if isinstance(it, str):
                        t = it.strip()
                        if t:
                            out.append(t)
                        continue
                    if isinstance(it, dict):
                        for k in ("label", "title", "name", "text", "content"):
                            vv = it.get(k)
                            if isinstance(vv, str) and vv.strip():
                                out.append(vv.strip())
                                break
                        continue
                    out.append(str(it))
                return out
            if isinstance(v, dict):
                for k in ("items", "bullets", "highlights", "paragraphs"):
                    if k in v:
                        return as_str_list(v.get(k))
            return [str(v)]

        if not isinstance(outline, dict):
            raise ValueError("outline must be an object")

        data = dict(outline)
        data.setdefault("title", topic)
        data.setdefault("audience", "通用受众")
        data.setdefault("tone", "清晰、教学")
        if theme:
            data["theme"] = theme
        data.setdefault("theme", "modern_blue")

        slides = data.get("slides")
        if not isinstance(slides, list):
            slides = []

        hydrated_slides = []
        for s in slides:
            if not isinstance(s, dict):
                continue
            slide = dict(s)
            if not slide.get("id"):
                slide["id"] = new_id("slide")
            notes = slide.get("notes")
            slide["notes"] = as_str_list(notes)

            intent = slide.get("intent")
            if intent == "agenda":
                slide["items"] = as_str_list(slide.get("items"))
            elif intent == "text":
                slide["paragraphs"] = as_str_list(slide.get("paragraphs"))
                slide["bullets"] = as_str_list(slide.get("bullets"))
                if not slide["paragraphs"] and isinstance(slide.get("content"), str) and slide.get("content").strip():
                    slide["paragraphs"] = [slide.get("content").strip()]
                slide.pop("content", None)
            elif intent == "kpi":
                items = slide.get("items")
                if isinstance(items, list):
                    out_items = []
                    for it in items:
                        if not isinstance(it, dict):
                            continue
                        item = dict(it)
                        if "value" in item and not isinstance(item["value"], str):
                            item["value"] = str(item["value"])
                        out_items.append(item)
                    slide["items"] = out_items
            hydrated_slides.append(slide)

        data["slides"] = hydrated_slides

        from ..domain.dsl import PresentationDSL

        return PresentationDSL.model_validate(data)

    def get(self, presentation_id: str) -> PresentationBundle:
        return self._repo.load(presentation_id)

    def list_themes(self):
        return {k: v.model_dump(by_alias=True) for k, v in DEFAULT_THEMES.items()}

    def patch_component(self, presentation_id: str, component_id: str, patch: ComponentPatch) -> PresentationBundle:
        bundle = self._repo.load(presentation_id)
        updated = False
        for slide in bundle.render_tree.slides:
            for comp in slide.components:
                if comp.id != component_id:
                    continue
                data = comp.model_dump(by_alias=True)
                patch_data = patch.model_dump(by_alias=True, exclude_none=True)
                if "style" in patch_data and patch_data["style"] is not None:
                    style = data.get("style") or {}
                    style.update(patch_data["style"])
                    patch_data["style"] = style
                if "props" in patch_data and patch_data["props"] is not None:
                    props = data.get("props") or {}
                    props.update(patch_data["props"])
                    patch_data["props"] = props
                data.update(patch_data)
                new_comp = comp.model_validate(data)
                comp.x = new_comp.x
                comp.y = new_comp.y
                comp.w = new_comp.w
                comp.h = new_comp.h
                comp.z = new_comp.z
                comp.rotation = new_comp.rotation
                comp.style = new_comp.style
                comp.props = new_comp.props
                updated = True
                break
        if not updated:
            raise KeyError(f"component not found: {component_id}")
        bundle.meta.updated_at = datetime.now(timezone.utc)
        bundle.meta.version += 1
        self._repo.save(bundle)
        return bundle

    def reorder_slides(self, presentation_id: str, slide_ids: List[str]) -> PresentationBundle:
        bundle = self._repo.load(presentation_id)
        by_id = {s.id: s for s in bundle.render_tree.slides}
        if set(slide_ids) != set(by_id.keys()):
            raise ValueError("slide_ids must contain exactly the current slides")
        bundle.render_tree.slides = [by_id[sid] for sid in slide_ids]

        dsl_by_id = {s.id: s for s in bundle.dsl.slides}
        if set(slide_ids) == set(dsl_by_id.keys()):
            bundle.dsl.slides = [dsl_by_id[sid] for sid in slide_ids]

        bundle.meta.updated_at = datetime.now(timezone.utc)
        bundle.meta.version += 1
        self._repo.save(bundle)
        return bundle

    def switch_theme(self, presentation_id: str, theme_name: str, rerender: bool = False) -> PresentationBundle:
        bundle = self._repo.load(presentation_id)
        tokens = get_theme_tokens(theme_name)
        bundle.dsl.theme = theme_name
        if rerender:
            bundle.render_tree = self._compiler.compile(presentation_id, bundle.dsl, tokens)
        bundle.render_tree.theme_name = theme_name
        bundle.render_tree.theme_tokens = tokens
        apply_theme_to_tree(bundle.render_tree, tokens)
        bundle.meta.updated_at = datetime.now(timezone.utc)
        bundle.meta.version += 1
        self._repo.save(bundle)
        return bundle

    def export_pptx(self, presentation_id: str) -> Path:
        bundle = self._repo.load(presentation_id)
        out_dir = Path(settings.data_dir) / "exports" / presentation_id
        out_path = out_dir / f"{presentation_id}.pptx"
        out_path = self._exporter.export(bundle.render_tree, out_path)
        bundle.last_export_pptx = str(out_path)
        bundle.meta.updated_at = datetime.now(timezone.utc)
        bundle.meta.version += 1
        self._repo.save(bundle)
        return out_path

    def regenerate(self, presentation_id: str, topic: Optional[str] = None, section: Optional[str] = None, use_rag: bool = True) -> PresentationBundle:
        bundle = self._repo.load(presentation_id)
        base_topic = topic or bundle.meta.topic
        rag_context = ""
        if use_rag and self._rag:
            rag_context = self._rag.retrieve_context(base_topic, top_k=5)
        new_dsl, ai_debug = self._ai.generate_dsl_with_debug(
            topic=base_topic, theme=bundle.dsl.theme, rag_context=rag_context
        )
        bundle.meta.extra = {"ai": ai_debug}
        if section:
            old_ids = [s.id for s in bundle.dsl.slides if getattr(s, "section", "") == section]
            new_slides = [s for s in new_dsl.slides if getattr(s, "section", "") == section]
            kept = [s for s in bundle.dsl.slides if s.id not in set(old_ids)]
            bundle.dsl.slides = kept + new_slides
        else:
            bundle.dsl = new_dsl
        tokens = get_theme_tokens(bundle.dsl.theme)
        bundle.render_tree = self._compiler.compile(presentation_id, bundle.dsl, tokens)
        apply_theme_to_tree(bundle.render_tree, tokens)
        bundle.meta.topic = base_topic
        bundle.meta.updated_at = datetime.now(timezone.utc)
        bundle.meta.version += 1
        self._repo.save(bundle)
        return bundle
