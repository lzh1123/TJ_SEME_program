from __future__ import annotations

from typing import Tuple

from ...domain.dsl import PresentationDSL
from ...domain.render_tree import RenderSlide, RenderTree
from ...domain.theme import ThemeTokens
from ...registry.base import Registry
from .layout import layout_components
from .planning import SlideComposer
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

    def compile(self, presentation_id: str, dsl: PresentationDSL, theme_tokens: ThemeTokens) -> RenderTree:
        slides_out = []
        padding = theme_tokens.spacing.slide_padding_px
        gap = theme_tokens.spacing.gap_px

        for slide in dsl.slides:
            composer = self._slide_composers.get(slide.intent)
            plan = composer.compose(slide)
            layout = self._layouts.get(plan.layout_id)
            comps = layout_components(layout, plan.components, self._slide_size, padding, gap)
            render_slide = RenderSlide(
                id=plan.slide_id,
                width=self._slide_size[0],
                height=self._slide_size[1],
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
            meta={"audience": dsl.audience, "tone": dsl.tone},
        )

