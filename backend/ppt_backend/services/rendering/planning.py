from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Protocol

from ...domain.dsl import (
    AgendaSlideDSL,
    ArchitectureSlideDSL,
    ChartSlideDSL,
    ComparisonSlideDSL,
    CoverSlideDSL,
    DividerSlideDSL,
    KpiSlideDSL,
    MultiColumnSlideDSL,
    ProcessFlowSlideDSL,
    QuoteSlideDSL,
    RoadmapSlideDSL,
    SwotSlideDSL,
    TeamSlideDSL,
    TextSlideDSL,
    TimelineSlideDSL,
)
from ...domain.render_tree import ComponentType


LayoutId = Literal[
    "cover",
    "title_body",
    "two_column",
    "grid_2x2",
    "timeline",
    "roadmap",
    "process_flow",
    "chart",
    "divider",
    "magazine_hero",
    "big_number_grid",
    "asymmetric_split",
    "card_masonry",
    "step_numbered",
    "quote_centered",
    "bento_grid",
    "gradient_overlay",
    "image_hero",
    "text_image_split",
]


@dataclass(frozen=True)
class ComponentBlueprint:
    component_id: str
    type: ComponentType
    props: Dict[str, Any] = field(default_factory=dict)
    slot: str = "content"
    z: int = 0


@dataclass(frozen=True)
class SlidePlan:
    slide_id: str
    layout_id: LayoutId
    title: str
    section: str
    notes: List[str]
    components: List[ComponentBlueprint]


class SlideComposer(Protocol):
    intent: str

    def compose(self, slide) -> SlidePlan: ...


class CoverComposer:
    intent = "cover"

    def compose(self, slide: CoverSlideDSL) -> SlidePlan:
        comps: List[ComponentBlueprint] = [
            ComponentBlueprint(
                component_id=f"{slide.id}__title",
                type="Title",
                props={"text": slide.title},
                slot="title",
                z=10,
            )
        ]
        if slide.subtitle:
            comps.append(
                ComponentBlueprint(
                    component_id=f"{slide.id}__subtitle",
                    type="Subtitle",
                    props={"text": slide.subtitle},
                    slot="subtitle",
                    z=10,
                )
            )
        if slide.tagline:
            comps.append(
                ComponentBlueprint(
                    component_id=f"{slide.id}__tagline",
                    type="Text",
                    props={"text": slide.tagline},
                    slot="tagline",
                    z=10,
                )
            )
        if slide.highlights:
            comps.append(
                ComponentBlueprint(
                    component_id=f"{slide.id}__highlights",
                    type="BulletList",
                    props={"items": slide.highlights},
                    slot="highlights",
                    z=10,
                )
            )
        if slide.image_query:
            comps.append(
                ComponentBlueprint(
                    component_id=f"{slide.id}__image",
                    type="Image",
                    props={"query": slide.image_query, "alt": slide.title, "fit": "cover"},
                    slot="visual",
                    z=5,
                )
            )
        return SlidePlan(
            slide_id=slide.id,
            layout_id="cover",
            title=slide.title,
            section=slide.section,
            notes=slide.notes,
            components=comps,
        )


class AgendaComposer:
    intent = "agenda"

    def compose(self, slide: AgendaSlideDSL) -> SlidePlan:
        comps = [
            ComponentBlueprint(
                component_id=f"{slide.id}__title",
                type="Title",
                props={"text": slide.title},
                slot="title",
                z=10,
            ),
            ComponentBlueprint(
                component_id=f"{slide.id}__bullets",
                type="BulletList",
                props={"items": slide.items},
                slot="body",
                z=10,
            ),
        ]
        return SlidePlan(
            slide_id=slide.id,
            layout_id="title_body",
            title=slide.title,
            section=slide.section,
            notes=slide.notes,
            components=comps,
        )


class TextComposer:
    intent = "text"

    def compose(self, slide: TextSlideDSL) -> SlidePlan:
        body_parts: List[str] = []
        body_parts.extend(slide.paragraphs)
        if slide.bullets:
            body_parts.append("")
            body_parts.extend([f"• {b}" for b in slide.bullets])
        comps = [
            ComponentBlueprint(
                component_id=f"{slide.id}__title",
                type="Title",
                props={"text": slide.title},
                slot="title",
                z=10,
            ),
            ComponentBlueprint(
                component_id=f"{slide.id}__text",
                type="Text",
                props={"text": "\n".join([p for p in body_parts if p is not None])},
                slot="text" if slide.image_query else "body",
                z=10,
            ),
        ]
        if slide.image_query:
            comps.append(
                ComponentBlueprint(
                    component_id=f"{slide.id}__image",
                    type="Image",
                    props={"query": slide.image_query, "alt": slide.title, "fit": "contain"},
                    slot="image",
                    z=5,
                )
            )
        return SlidePlan(
            slide_id=slide.id,
            layout_id="text_image_split" if slide.image_query else "title_body",
            title=slide.title,
            section=slide.section,
            notes=slide.notes,
            components=comps,
        )


class TimelineComposer:
    intent = "timeline"

    def compose(self, slide: TimelineSlideDSL) -> SlidePlan:
        comps = [
            ComponentBlueprint(
                component_id=f"{slide.id}__title",
                type="Title",
                props={"text": slide.title},
                slot="title",
                z=10,
            ),
            ComponentBlueprint(
                component_id=f"{slide.id}__timeline",
                type="Timeline",
                props={"events": [e.model_dump() for e in slide.events]},
                slot="body",
                z=10,
            ),
        ]
        return SlidePlan(
            slide_id=slide.id,
            layout_id="timeline",
            title=slide.title,
            section=slide.section,
            notes=slide.notes,
            components=comps,
        )


class KpiComposer:
    intent = "kpi"

    def compose(self, slide: KpiSlideDSL) -> SlidePlan:
        comps = [
            ComponentBlueprint(
                component_id=f"{slide.id}__title",
                type="Title",
                props={"text": slide.title},
                slot="title",
                z=10,
            ),
            ComponentBlueprint(
                component_id=f"{slide.id}__kpi",
                type="KpiCards",
                props={"items": [i.model_dump() for i in slide.items]},
                slot="body",
                z=10,
            ),
        ]
        return SlidePlan(
            slide_id=slide.id,
            layout_id="title_body",
            title=slide.title,
            section=slide.section,
            notes=slide.notes,
            components=comps,
        )


class ComparisonComposer:
    intent = "comparison"

    def compose(self, slide: ComparisonSlideDSL) -> SlidePlan:
        comps = [
            ComponentBlueprint(
                component_id=f"{slide.id}__title",
                type="Title",
                props={"text": slide.title},
                slot="title",
                z=10,
            ),
            ComponentBlueprint(
                component_id=f"{slide.id}__comparison",
                type="ComparisonTable",
                props={
                    "left": slide.left.model_dump(),
                    "right": slide.right.model_dump(),
                },
                slot="body",
                z=10,
            ),
        ]
        return SlidePlan(
            slide_id=slide.id,
            layout_id="two_column",
            title=slide.title,
            section=slide.section,
            notes=slide.notes,
            components=comps,
        )


class SwotComposer:
    intent = "swot"

    def compose(self, slide: SwotSlideDSL) -> SlidePlan:
        comps = [
            ComponentBlueprint(
                component_id=f"{slide.id}__title",
                type="Title",
                props={"text": slide.title},
                slot="title",
                z=10,
            ),
            ComponentBlueprint(
                component_id=f"{slide.id}__swot",
                type="Swot",
                props=slide.swot.model_dump(),
                slot="body",
                z=10,
            ),
        ]
        return SlidePlan(
            slide_id=slide.id,
            layout_id="grid_2x2",
            title=slide.title,
            section=slide.section,
            notes=slide.notes,
            components=comps,
        )


class RoadmapComposer:
    intent = "roadmap"

    def compose(self, slide: RoadmapSlideDSL) -> SlidePlan:
        comps = [
            ComponentBlueprint(
                component_id=f"{slide.id}__title",
                type="Title",
                props={"text": slide.title},
                slot="title",
                z=10,
            ),
            ComponentBlueprint(
                component_id=f"{slide.id}__roadmap",
                type="Roadmap",
                props={"phases": [p.model_dump() for p in slide.phases]},
                slot="body",
                z=10,
            ),
        ]
        return SlidePlan(
            slide_id=slide.id,
            layout_id="roadmap",
            title=slide.title,
            section=slide.section,
            notes=slide.notes,
            components=comps,
        )


class ProcessFlowComposer:
    intent = "process_flow"

    def compose(self, slide: ProcessFlowSlideDSL) -> SlidePlan:
        comps = [
            ComponentBlueprint(
                component_id=f"{slide.id}__title",
                type="Title",
                props={"text": slide.title},
                slot="title",
                z=10,
            ),
            ComponentBlueprint(
                component_id=f"{slide.id}__process",
                type="ProcessFlow",
                props={"steps": [s.model_dump() for s in slide.steps]},
                slot="body",
                z=10,
            ),
        ]
        return SlidePlan(
            slide_id=slide.id,
            layout_id="process_flow",
            title=slide.title,
            section=slide.section,
            notes=slide.notes,
            components=comps,
        )


class ChartComposer:
    intent = "chart"

    def compose(self, slide: ChartSlideDSL) -> SlidePlan:
        comps = [
            ComponentBlueprint(
                component_id=f"{slide.id}__title",
                type="Title",
                props={"text": slide.title},
                slot="title",
                z=10,
            ),
            ComponentBlueprint(
                component_id=f"{slide.id}__chart",
                type="Chart",
                props=slide.chart.model_dump(by_alias=True),
                slot="body",
                z=10,
            ),
        ]
        return SlidePlan(
            slide_id=slide.id,
            layout_id="chart",
            title=slide.title,
            section=slide.section,
            notes=slide.notes,
            components=comps,
        )


class MultiColumnComposer:
    intent = "multi_column"

    def compose(self, slide: MultiColumnSlideDSL) -> SlidePlan:
        comps = [
            ComponentBlueprint(
                component_id=f"{slide.id}__title",
                type="Title",
                props={"text": slide.title},
                slot="title",
                z=10,
            ),
            ComponentBlueprint(
                component_id=f"{slide.id}__columns",
                type="MultiColumn",
                props={"columns": [c.model_dump() for c in slide.columns]},
                slot="body",
                z=10,
            ),
        ]
        return SlidePlan(
            slide_id=slide.id,
            layout_id="two_column",
            title=slide.title,
            section=slide.section,
            notes=slide.notes,
            components=comps,
        )


class ArchitectureComposer:
    intent = "architecture"

    def compose(self, slide: ArchitectureSlideDSL) -> SlidePlan:
        comps = [
            ComponentBlueprint(
                component_id=f"{slide.id}__title",
                type="Title",
                props={"text": slide.title},
                slot="title",
                z=10,
            ),
            ComponentBlueprint(
                component_id=f"{slide.id}__arch",
                type="ArchitectureDiagram",
                props={"layers": [l.model_dump() for l in slide.layers]},
                slot="body",
                z=10,
            ),
        ]
        return SlidePlan(
            slide_id=slide.id,
            layout_id="title_body",
            title=slide.title,
            section=slide.section,
            notes=slide.notes,
            components=comps,
        )


class QuoteComposer:
    intent = "quote"

    def compose(self, slide: QuoteSlideDSL) -> SlidePlan:
        comps = [
            ComponentBlueprint(
                component_id=f"{slide.id}__quote",
                type="Quote",
                props={"quote": slide.quote, "author": slide.author},
                slot="body",
                z=10,
            )
        ]
        return SlidePlan(
            slide_id=slide.id,
            layout_id="title_body",
            title=slide.title,
            section=slide.section,
            notes=slide.notes,
            components=comps,
        )


class DividerComposer:
    intent = "divider"

    def compose(self, slide: DividerSlideDSL) -> SlidePlan:
        comps = [
            ComponentBlueprint(
                component_id=f"{slide.id}__divider",
                type="Divider",
                props={"title": slide.title, "subtitle": slide.subtitle},
                slot="body",
                z=10,
            )
        ]
        if slide.image_query:
            comps.append(
                ComponentBlueprint(
                    component_id=f"{slide.id}__bg_image",
                    type="Image",
                    props={"query": slide.image_query, "alt": slide.title, "fit": "cover"},
                    slot="body",
                    z=1,
                )
            )
        return SlidePlan(
            slide_id=slide.id,
            layout_id="gradient_overlay",
            title=slide.title,
            section=slide.section,
            notes=slide.notes,
            components=comps,
        )


class TeamComposer:
    intent = "team"

    def compose(self, slide: TeamSlideDSL) -> SlidePlan:
        comps = [
            ComponentBlueprint(
                component_id=f"{slide.id}__title",
                type="Title",
                props={"text": slide.title},
                slot="title",
                z=10,
            ),
            ComponentBlueprint(
                component_id=f"{slide.id}__team",
                type="TeamCards",
                props={"members": [m.model_dump() for m in slide.members]},
                slot="body",
                z=10,
            ),
        ]
        return SlidePlan(
            slide_id=slide.id,
            layout_id="title_body",
            title=slide.title,
            section=slide.section,
            notes=slide.notes,
            components=comps,
        )

