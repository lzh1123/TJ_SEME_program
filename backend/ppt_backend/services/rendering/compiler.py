from __future__ import annotations

from typing import Tuple

from ...domain.dsl import PresentationDSL
from ...domain.render_tree import RenderSlide, RenderTree
from ...domain.theme import ThemeTokens
from ...registry.base import Registry
from .layout import layout_components
from .layout_selector import select_layout
from .planning import SlideComposer, SlidePlan
from .theme_engine import apply_theme_to_slide


class RenderCompiler:
    def __init__(
        self,
        slide_composers: Registry[SlideComposer],
        layouts: Registry,
        slide_size: Tuple[int, int] = (1280, 720),
    ):
        self._slide_composers = slide_composers
        self._layouts = layouts
        self._slide_size = slide_size

    def compile(
        self,
        presentation_id: str,
        dsl: PresentationDSL,
        theme_tokens: ThemeTokens,
        rag_images: list = None,
    ) -> RenderTree:
        slides_out = []
        padding = theme_tokens.spacing.slide_padding_px
        gap = theme_tokens.spacing.gap_px

        # Build image lookup: slide_id -> [image dicts]
        image_map: dict = {}
        if rag_images:
            for slide in dsl.slides:
                image_query = getattr(slide, "image_query", None)
                if image_query:
                    for img in rag_images:
                        url = img.get("url", "")
                        if url and image_map.get(slide.id) is None:
                            image_map[slide.id] = []
                        if url:
                            image_map.setdefault(slide.id, []).append(img)
                            break

        for slide in dsl.slides:
            composer = self._slide_composers.get(slide.intent)
            plan: SlidePlan = composer.compose(slide)

            has_image = slide.id in image_map
            item_count = 0
            step_count = 0
            column_count = 0

            if slide.intent in ("kpi", "agenda", "team"):
                items = getattr(slide, "items", None) or getattr(slide, "members", None)
                item_count = len(items) if items else 0
            if slide.intent == "process_flow":
                steps = getattr(slide, "steps", None)
                step_count = len(steps) if steps else 0
            if slide.intent == "multi_column":
                cols = getattr(slide, "columns", None)
                column_count = len(cols) if cols else 0

            selected_layout_id = select_layout(
                intent=slide.intent,
                content_count=len(plan.components),
                has_image=has_image,
                item_count=item_count,
                step_count=step_count,
                column_count=column_count,
            )

            layout = self._layouts.get(selected_layout_id)
            if layout is None:
                layout = self._layouts.get(plan.layout_id)

            comps = layout_components(layout, plan.components, self._slide_size, padding, gap)

            # Set slide background image if available
            background = None
            background_image = None
            if has_image:
                img = image_map[slide.id][0]
                if selected_layout_id in ("image_hero", "gradient_overlay", "cover", "magazine_hero"):
                    background_image = img.get("url")

            render_slide = RenderSlide(
                id=plan.slide_id,
                width=self._slide_size[0],
                height=self._slide_size[1],
                background=background,
                background_image=background_image,
                components=comps,
                notes=plan.notes,
            )
            render_slide = apply_theme_to_slide(render_slide, theme_tokens)
            slides_out.append(render_slide)

        return RenderTree(
            presentationId=presentation_id,
            title=dsl.title,
            themeName=dsl.theme,
            themeTokens=theme_tokens,
            slides=slides_out,
            meta={
                "audience": dsl.audience,
                "tone": dsl.tone,
                "images": {sid: [img["url"] for img in imgs] for sid, imgs in image_map.items()},
            },
        )

