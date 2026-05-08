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
    ):
        self._repo = repo
        self._ai = ai
        self._compiler = compiler
        self._exporter = exporter

    def create(self, topic: str, theme: Optional[str] = None) -> PresentationBundle:
        presentation_id = new_id("pres")
        dsl = self._ai.generate_dsl(topic=topic, theme=theme)
        theme_tokens = get_theme_tokens(dsl.theme)
        tree = self._compiler.compile(presentation_id, dsl, theme_tokens)
        tree = apply_theme_to_tree(tree, theme_tokens)
        meta = PresentationMeta(id=presentation_id, topic=topic)
        bundle = PresentationBundle(meta=meta, dsl=dsl, renderTree=tree)
        self._repo.save(bundle)
        return bundle

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

    def regenerate(self, presentation_id: str, topic: Optional[str] = None, section: Optional[str] = None) -> PresentationBundle:
        bundle = self._repo.load(presentation_id)
        base_topic = topic or bundle.meta.topic
        new_dsl = self._ai.generate_dsl(topic=base_topic, theme=bundle.dsl.theme)
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

