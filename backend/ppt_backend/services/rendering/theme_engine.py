from __future__ import annotations

from ...domain.render_tree import ComponentSpec, RenderSlide, RenderTree, StyleSpec
from ...domain.theme import ThemeTokens


def _default_style_for(component_type: str, theme: ThemeTokens) -> StyleSpec:
    colors = theme.colors
    typo = theme.typography
    if component_type == "Title":
        return StyleSpec(
            color=colors.text,
            fontFamily=typo.font_family,
            fontSize=typo.title_pt,
            bold=True,
            align="left",
        )
    if component_type == "Subtitle":
        return StyleSpec(
            color=colors.muted,
            fontFamily=typo.font_family,
            fontSize=typo.subtitle_pt,
            bold=False,
            align="left",
        )
    if component_type in {"Text", "BulletList", "Timeline", "ProcessFlow", "Roadmap", "ArchitectureDiagram"}:
        return StyleSpec(
            color=colors.text,
            fontFamily=typo.font_family,
            fontSize=typo.body_pt,
            bold=False,
            align="left",
        )
    if component_type in {"KpiCards", "ComparisonTable", "Swot", "MultiColumn", "TeamCards", "Statistics"}:
        return StyleSpec(
            color=colors.text,
            background=colors.surface,
            borderColor=colors.border,
            borderWidth=1,
            radius=12,
            fontFamily=typo.font_family,
            fontSize=typo.body_pt,
            bold=False,
            align="left",
        )
    if component_type == "Quote":
        return StyleSpec(
            color=colors.text,
            background=colors.surface,
            borderColor=colors.primary,
            borderWidth=2,
            radius=16,
            fontFamily=typo.font_family,
            fontSize=typo.subtitle_pt,
            italic=True,
            align="center",
        )
    if component_type == "Divider":
        return StyleSpec(
            color=colors.text,
            background=colors.background,
            fontFamily=typo.font_family,
            fontSize=typo.title_pt,
            bold=True,
            align="center",
        )
    if component_type == "Chart":
        return StyleSpec(
            color=colors.text,
            background=colors.surface,
            borderColor=colors.border,
            borderWidth=1,
            radius=12,
            fontFamily=typo.font_family,
            fontSize=typo.body_pt,
            bold=False,
            align="left",
        )
    return StyleSpec(
        color=colors.text,
        fontFamily=typo.font_family,
        fontSize=typo.body_pt,
        bold=False,
        align="left",
    )


def apply_theme_to_tree(tree: RenderTree, theme_tokens: ThemeTokens) -> RenderTree:
    for slide in tree.slides:
        slide.background = slide.background or theme_tokens.colors.background
        for comp in slide.components:
            defaults = _default_style_for(comp.type, theme_tokens)
            merged = defaults.model_dump(by_alias=True, exclude_none=True)
            merged.update(comp.style.model_dump(by_alias=True, exclude_none=True))
            comp.style = StyleSpec.model_validate(merged)
    tree.theme_tokens = theme_tokens
    return tree


def apply_theme_to_slide(slide: RenderSlide, theme_tokens: ThemeTokens) -> RenderSlide:
    slide.background = slide.background or theme_tokens.colors.background
    for comp in slide.components:
        defaults = _default_style_for(comp.type, theme_tokens)
        merged = defaults.model_dump(by_alias=True, exclude_none=True)
        merged.update(comp.style.model_dump(by_alias=True, exclude_none=True))
        comp.style = StyleSpec.model_validate(merged)
    return slide

