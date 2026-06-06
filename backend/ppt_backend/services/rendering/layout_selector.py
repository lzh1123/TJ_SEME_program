from __future__ import annotations

from typing import Optional

from .planning import LayoutId


def select_layout(
    intent: str,
    content_count: int = 0,
    has_image: bool = False,
    item_count: int = 0,
    step_count: int = 0,
    column_count: int = 0,
) -> LayoutId:
    """Deterministic layout selection based on content characteristics.

    Args:
        intent: Slide intent (cover, text, kpi, comparison, etc.)
        content_count: Total number of content elements
        has_image: Whether slide has an associated image
        item_count: For KPI/agenda/team slides, number of items
        step_count: For process flows, number of steps
        column_count: For multi-column slides, number of columns
    """
    # Cover: use magazine_hero for rich covers
    if intent == "cover":
        if has_image or content_count >= 6:
            return "magazine_hero"
        return "cover"

    # Agenda
    if intent == "agenda":
        return "title_body"

    # Text: use asymmetric_split when image is available
    if intent == "text":
        if has_image:
            return "asymmetric_split"
        return "title_body"

    # Timeline
    if intent == "timeline":
        return "timeline"

    # KPI: big_number_grid for 4+ items
    if intent == "kpi":
        if item_count >= 4:
            return "big_number_grid"
        return "title_body"

    # Comparison: asymmetric_split when image available
    if intent == "comparison":
        if has_image:
            return "asymmetric_split"
        return "two_column"

    # SWOT: bento_grid for richer layout
    if intent == "swot":
        return "bento_grid"

    # Roadmap
    if intent == "roadmap":
        return "roadmap"

    # Process flow: step_numbered for <=6 steps, else title_body
    if intent == "process_flow":
        if step_count <= 6:
            return "step_numbered"
        return "process_flow"

    # Chart
    if intent == "chart":
        return "chart"

    # Multi-column: card_masonry for 3 columns, else two_column
    if intent == "multi_column":
        if column_count == 3:
            return "card_masonry"
        return "two_column"

    # Architecture
    if intent == "architecture":
        return "title_body"

    # Quote: quote_centered for modern look
    if intent == "quote":
        return "quote_centered"

    # Divider: gradient_overlay
    if intent == "divider":
        return "gradient_overlay"

    # Team: card_masonry for 3 members
    if intent == "team":
        if item_count == 3:
            return "card_masonry"
        return "title_body"

    # Default fallback
    return "title_body"
