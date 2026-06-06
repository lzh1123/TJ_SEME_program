from __future__ import annotations

from ...registry.base import Registry
from .layout import (
    ChartLayout,
    CoverLayout,
    DividerLayout,
    Grid2x2Layout,
    ProcessFlowLayout,
    RoadmapLayout,
    TimelineLayout,
    TitleBodyLayout,
    TwoColumnLayout,
)
from .planning import (
    AgendaComposer,
    ArchitectureComposer,
    ChartComposer,
    ComparisonComposer,
    CoverComposer,
    DividerComposer,
    KpiComposer,
    MultiColumnComposer,
    ProcessFlowComposer,
    QuoteComposer,
    RoadmapComposer,
    SlideComposer,
    SwotComposer,
    TeamComposer,
    TextComposer,
    TimelineComposer,
)


def build_slide_composer_registry() -> Registry[SlideComposer]:
    reg: Registry[SlideComposer] = Registry()
    for composer in [
        CoverComposer(),
        AgendaComposer(),
        TextComposer(),
        TimelineComposer(),
        KpiComposer(),
        ComparisonComposer(),
        SwotComposer(),
        RoadmapComposer(),
        ProcessFlowComposer(),
        ChartComposer(),
        MultiColumnComposer(),
        ArchitectureComposer(),
        QuoteComposer(),
        DividerComposer(),
        TeamComposer(),
    ]:
        reg.register(composer.intent, composer)
    return reg


def build_layout_registry():
    reg = Registry()
    for layout in [
        CoverLayout(),
        TitleBodyLayout(),
        TwoColumnLayout(),
        Grid2x2Layout(),
        TimelineLayout(),
        RoadmapLayout(),
        ProcessFlowLayout(),
        ChartLayout(),
        DividerLayout(),
    ]:
        reg.register(layout.layout_id, layout)
    return reg
