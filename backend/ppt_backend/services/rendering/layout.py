from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Protocol, Tuple

from ...domain.render_tree import ComponentSpec
from .planning import ComponentBlueprint, LayoutId


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    w: float
    h: float


class LayoutTemplate(Protocol):
    layout_id: LayoutId

    def slot_rects(
        self,
        slide_size: Tuple[int, int],
        padding_px: int,
        gap_px: int,
    ) -> Dict[str, Rect]: ...


def _place_by_slot(blueprints: List[ComponentBlueprint], slots: Dict[str, Rect]) -> List[ComponentSpec]:
    out: List[ComponentSpec] = []
    for bp in blueprints:
        rect = slots.get(bp.slot) or slots.get("body") or Rect(0, 0, 1280, 720)
        out.append(
            ComponentSpec(
                id=bp.component_id,
                type=bp.type,
                x=rect.x,
                y=rect.y,
                w=rect.w,
                h=rect.h,
                z=bp.z,
                props=dict(bp.props),
            )
        )
    out.sort(key=lambda c: c.z)
    return out


class CoverLayout:
    layout_id: LayoutId = "cover"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        w, h = slide_size
        x0 = padding_px
        y0 = padding_px
        cw = w - 2 * padding_px
        title_h = 120
        subtitle_h = 70
        tagline_h = 60
        highlights_h = max(180, h - (y0 + title_h + subtitle_h + tagline_h + 4 * gap_px) - padding_px)
        return {
            "title": Rect(x0, y0, cw, title_h),
            "subtitle": Rect(x0, y0 + title_h + gap_px, cw, subtitle_h),
            "tagline": Rect(x0, y0 + title_h + subtitle_h + 2 * gap_px, cw, tagline_h),
            "highlights": Rect(
                x0,
                y0 + title_h + subtitle_h + tagline_h + 3 * gap_px,
                cw,
                highlights_h,
            ),
            "body": Rect(x0, y0, cw, h - 2 * padding_px),
        }


class TitleBodyLayout:
    layout_id: LayoutId = "title_body"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        w, h = slide_size
        x0 = padding_px
        y0 = padding_px
        cw = w - 2 * padding_px
        title_h = 96
        return {
            "title": Rect(x0, y0, cw, title_h),
            "body": Rect(x0, y0 + title_h + gap_px, cw, h - (y0 + title_h + gap_px) - padding_px),
        }


class TwoColumnLayout:
    layout_id: LayoutId = "two_column"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        w, h = slide_size
        x0 = padding_px
        y0 = padding_px
        cw = w - 2 * padding_px
        title_h = 96
        body_y = y0 + title_h + gap_px
        body_h = h - body_y - padding_px
        col_w = (cw - gap_px) / 2
        return {
            "title": Rect(x0, y0, cw, title_h),
            "left": Rect(x0, body_y, col_w, body_h),
            "right": Rect(x0 + col_w + gap_px, body_y, col_w, body_h),
            "body": Rect(x0, body_y, cw, body_h),
        }


class Grid2x2Layout:
    layout_id: LayoutId = "grid_2x2"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        w, h = slide_size
        x0 = padding_px
        y0 = padding_px
        cw = w - 2 * padding_px
        title_h = 96
        body_y = y0 + title_h + gap_px
        body_h = h - body_y - padding_px
        cell_w = (cw - gap_px) / 2
        cell_h = (body_h - gap_px) / 2
        return {
            "title": Rect(x0, y0, cw, title_h),
            "cell_1": Rect(x0, body_y, cell_w, cell_h),
            "cell_2": Rect(x0 + cell_w + gap_px, body_y, cell_w, cell_h),
            "cell_3": Rect(x0, body_y + cell_h + gap_px, cell_w, cell_h),
            "cell_4": Rect(x0 + cell_w + gap_px, body_y + cell_h + gap_px, cell_w, cell_h),
            "body": Rect(x0, body_y, cw, body_h),
        }


class TimelineLayout:
    layout_id: LayoutId = "timeline"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        return TitleBodyLayout().slot_rects(slide_size, padding_px, gap_px)


class RoadmapLayout:
    layout_id: LayoutId = "roadmap"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        return TitleBodyLayout().slot_rects(slide_size, padding_px, gap_px)


class ProcessFlowLayout:
    layout_id: LayoutId = "process_flow"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        return TitleBodyLayout().slot_rects(slide_size, padding_px, gap_px)


class ChartLayout:
    layout_id: LayoutId = "chart"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        return TitleBodyLayout().slot_rects(slide_size, padding_px, gap_px)


class DividerLayout:
    layout_id: LayoutId = "divider"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        w, h = slide_size
        x0 = padding_px
        y0 = padding_px
        cw = w - 2 * padding_px
        body_h = h - 2 * padding_px
        return {"body": Rect(x0, y0, cw, body_h)}


def _title_height(slide_h: int, padding_px: int, ratio: float = 1.618) -> float:
    """Title area height based on golden ratio."""
    available = slide_h - 2 * padding_px
    return available / (1 + ratio)


class MagazineHeroLayout:
    layout_id: LayoutId = "magazine_hero"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        w, h = slide_size
        x0 = padding_px
        y0 = padding_px
        cw = w - 2 * padding_px
        ch = h - 2 * padding_px
        left_w = cw * 0.38
        right_w = cw * 0.62 - gap_px
        title_h = 120
        subtitle_h = 70
        tagline_h = 60
        highlights_y = y0 + title_h + subtitle_h + tagline_h + 3 * gap_px
        highlights_h = max(120, h - highlights_y - padding_px)
        return {
            "title": Rect(x0, y0, left_w, title_h),
            "subtitle": Rect(x0, y0 + title_h + gap_px, left_w, subtitle_h),
            "tagline": Rect(x0, y0 + title_h + subtitle_h + 2 * gap_px, left_w, tagline_h),
            "highlights": Rect(x0, highlights_y, left_w, highlights_h),
            "visual": Rect(x0 + left_w + gap_px, y0, right_w, ch),
            "body": Rect(x0, y0, cw, ch),
        }


class BigNumberGridLayout:
    layout_id: LayoutId = "big_number_grid"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        w, h = slide_size
        x0 = padding_px
        y0 = padding_px
        cw = w - 2 * padding_px
        title_h = _title_height(h, padding_px)
        body_y = y0 + title_h + gap_px
        body_h = h - body_y - padding_px
        cell_w = (cw - gap_px) / 2
        cell_h = (body_h - gap_px) / 2
        return {
            "title": Rect(x0, y0, cw, title_h),
            "cell_1": Rect(x0, body_y, cell_w, cell_h),
            "cell_2": Rect(x0 + cell_w + gap_px, body_y, cell_w, cell_h),
            "cell_3": Rect(x0, body_y + cell_h + gap_px, cell_w, cell_h),
            "cell_4": Rect(x0 + cell_w + gap_px, body_y + cell_h + gap_px, cell_w, cell_h),
            "body": Rect(x0, body_y, cw, body_h),
        }


class AsymmetricSplitLayout:
    layout_id: LayoutId = "asymmetric_split"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        w, h = slide_size
        x0 = padding_px
        y0 = padding_px
        cw = w - 2 * padding_px
        title_h = _title_height(h, padding_px)
        body_y = y0 + title_h + gap_px
        body_h = h - body_y - padding_px
        left_w = cw * 0.62 - gap_px / 2
        right_w = cw * 0.38 - gap_px / 2
        return {
            "title": Rect(x0, y0, cw, title_h),
            "left": Rect(x0, body_y, left_w, body_h),
            "right": Rect(x0 + left_w + gap_px, body_y, right_w, body_h),
            "body": Rect(x0, body_y, cw, body_h),
        }


class CardMasonryLayout:
    layout_id: LayoutId = "card_masonry"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        w, h = slide_size
        x0 = padding_px
        y0 = padding_px
        cw = w - 2 * padding_px
        title_h = _title_height(h, padding_px)
        body_y = y0 + title_h + gap_px
        body_h = h - body_y - padding_px
        cell_w = (cw - gap_px) / 2
        cell_h = (body_h - gap_px) / 2
        bottom_w = cw * 0.5
        bottom_x = x0 + (cw - bottom_w) / 2
        return {
            "title": Rect(x0, y0, cw, title_h),
            "cell_1": Rect(x0, body_y, cell_w, cell_h),
            "cell_2": Rect(x0 + cell_w + gap_px, body_y, cell_w, cell_h),
            "cell_3": Rect(bottom_x, body_y + cell_h + gap_px, bottom_w, cell_h),
            "body": Rect(x0, body_y, cw, body_h),
        }


class StepNumberedLayout:
    layout_id: LayoutId = "step_numbered"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        w, h = slide_size
        x0 = padding_px
        y0 = padding_px
        cw = w - 2 * padding_px
        title_h = _title_height(h, padding_px)
        body_y = y0 + title_h + gap_px
        body_h = h - body_y - padding_px
        return {
            "title": Rect(x0, y0, cw, title_h),
            "body": Rect(x0, body_y, cw, body_h),
        }


class QuoteCenteredLayout:
    layout_id: LayoutId = "quote_centered"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        w, h = slide_size
        margin_x = w * 0.15
        margin_y = h * 0.2
        body_w = w - 2 * margin_x
        body_h = h - 2 * margin_y
        return {
            "body": Rect(margin_x, margin_y, body_w, body_h),
        }


class BentoGridLayout:
    layout_id: LayoutId = "bento_grid"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        w, h = slide_size
        x0 = padding_px
        y0 = padding_px
        cw = w - 2 * padding_px
        title_h = _title_height(h, padding_px)
        body_y = y0 + title_h + gap_px
        body_h = h - body_y - padding_px
        col_w = (cw - gap_px) / 2
        return {
            "title": Rect(x0, y0, cw, title_h),
            "cell_1": Rect(x0, body_y, col_w, body_h),
            "cell_2": Rect(x0 + col_w + gap_px, body_y, col_w, (body_h - gap_px) / 2),
            "cell_3": Rect(x0 + col_w + gap_px, body_y + (body_h - gap_px) / 2 + gap_px, col_w, (body_h - gap_px) / 2),
            "body": Rect(x0, body_y, cw, body_h),
        }


class GradientOverlayLayout:
    layout_id: LayoutId = "gradient_overlay"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        w, h = slide_size
        x0 = padding_px
        y0 = h * 0.3
        cw = w - 2 * padding_px
        body_h = h * 0.4
        return {
            "title": Rect(x0, y0 - 60, cw, 50),
            "subtitle": Rect(x0, y0 + body_h - 50, cw, 40),
            "body": Rect(x0, y0, cw, body_h),
        }


class ImageHeroLayout:
    layout_id: LayoutId = "image_hero"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        w, h = slide_size
        x0 = padding_px
        cw = w - 2 * padding_px
        title_y = h * 0.55
        title_h = 80
        subtitle_y = title_y + title_h + gap_px
        subtitle_h = 50
        return {
            "title": Rect(x0, title_y, cw, title_h),
            "subtitle": Rect(x0, subtitle_y, cw, subtitle_h),
            "body": Rect(x0, padding_px, cw, h - 2 * padding_px),
        }


class TextImageSplitLayout:
    layout_id: LayoutId = "text_image_split"

    def slot_rects(self, slide_size: Tuple[int, int], padding_px: int, gap_px: int) -> Dict[str, Rect]:
        w, h = slide_size
        x0 = padding_px
        y0 = padding_px
        cw = w - 2 * padding_px
        title_h = _title_height(h, padding_px)
        body_y = y0 + title_h + gap_px
        body_h = h - body_y - padding_px
        text_w = cw * 0.55 - gap_px / 2
        image_w = cw * 0.45 - gap_px / 2
        return {
            "title": Rect(x0, y0, cw, title_h),
            "text": Rect(x0, body_y, text_w, body_h),
            "image": Rect(x0 + text_w + gap_px, body_y, image_w, body_h),
            "body": Rect(x0, body_y, cw, body_h),
        }


def layout_components(
    layout: LayoutTemplate,
    blueprints: List[ComponentBlueprint],
    slide_size: Tuple[int, int],
    padding_px: int,
    gap_px: int,
) -> List[ComponentSpec]:
    slots = layout.slot_rects(slide_size, padding_px, gap_px)
    return _place_by_slot(blueprints, slots)

