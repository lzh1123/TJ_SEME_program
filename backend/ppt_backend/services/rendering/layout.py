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


def layout_components(
    layout: LayoutTemplate,
    blueprints: List[ComponentBlueprint],
    slide_size: Tuple[int, int],
    padding_px: int,
    gap_px: int,
) -> List[ComponentSpec]:
    slots = layout.slot_rects(slide_size, padding_px, gap_px)
    return _place_by_slot(blueprints, slots)

