from __future__ import annotations

from typing import Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class TimelineEvent(BaseModel):
    model_config = {"extra": "forbid"}

    label: str
    date: Optional[str] = None
    detail: Optional[str] = None


class KPIItem(BaseModel):
    model_config = {"extra": "forbid"}

    label: str
    value: str
    unit: Optional[str] = None
    delta: Optional[str] = None


class ComparisonSide(BaseModel):
    model_config = {"extra": "forbid"}

    title: str
    bullets: List[str] = Field(default_factory=list)


class SwotBlock(BaseModel):
    model_config = {"extra": "forbid"}

    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    threats: List[str] = Field(default_factory=list)


class RoadmapPhase(BaseModel):
    model_config = {"extra": "forbid"}

    name: str
    timeframe: Optional[str] = None
    deliverables: List[str] = Field(default_factory=list)


class ProcessStep(BaseModel):
    model_config = {"extra": "forbid"}

    name: str
    detail: Optional[str] = None


class ChartSeries(BaseModel):
    model_config = {"extra": "forbid"}

    name: str
    values: List[float]


class ChartSemantic(BaseModel):
    model_config = {"extra": "forbid"}

    chart_type: Literal["bar", "line", "pie"] = Field(alias="chartType")
    labels: List[str] = Field(default_factory=list)
    series: List[ChartSeries] = Field(default_factory=list)


class ColumnBlock(BaseModel):
    model_config = {"extra": "forbid"}

    title: str
    bullets: List[str] = Field(default_factory=list)


class ArchitectureLayer(BaseModel):
    model_config = {"extra": "forbid"}

    name: str
    items: List[str] = Field(default_factory=list)


class TeamMember(BaseModel):
    model_config = {"extra": "forbid"}

    name: str
    role: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)


class BaseSlideDSL(BaseModel):
    model_config = {"extra": "forbid"}

    id: str
    intent: str
    section: str = ""
    title: str
    notes: List[str] = Field(default_factory=list)
    image_query: Optional[str] = None


class CoverSlideDSL(BaseSlideDSL):
    model_config = {"extra": "forbid"}

    intent: Literal["cover"]
    subtitle: Optional[str] = None
    tagline: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)


class AgendaSlideDSL(BaseSlideDSL):
    model_config = {"extra": "forbid"}

    intent: Literal["agenda"]
    items: List[str] = Field(default_factory=list)


class TextSlideDSL(BaseSlideDSL):
    model_config = {"extra": "forbid"}

    intent: Literal["text"]
    paragraphs: List[str] = Field(default_factory=list)
    bullets: List[str] = Field(default_factory=list)


class TimelineSlideDSL(BaseSlideDSL):
    model_config = {"extra": "forbid"}

    intent: Literal["timeline"]
    events: List[TimelineEvent] = Field(default_factory=list)


class KpiSlideDSL(BaseSlideDSL):
    model_config = {"extra": "forbid"}

    intent: Literal["kpi"]
    items: List[KPIItem] = Field(default_factory=list)


class ComparisonSlideDSL(BaseSlideDSL):
    model_config = {"extra": "forbid"}

    intent: Literal["comparison"]
    left: ComparisonSide
    right: ComparisonSide


class SwotSlideDSL(BaseSlideDSL):
    model_config = {"extra": "forbid"}

    intent: Literal["swot"]
    swot: SwotBlock


class RoadmapSlideDSL(BaseSlideDSL):
    model_config = {"extra": "forbid"}

    intent: Literal["roadmap"]
    phases: List[RoadmapPhase] = Field(default_factory=list)


class ProcessFlowSlideDSL(BaseSlideDSL):
    model_config = {"extra": "forbid"}

    intent: Literal["process_flow"]
    steps: List[ProcessStep] = Field(default_factory=list)


class ChartSlideDSL(BaseSlideDSL):
    model_config = {"extra": "forbid"}

    intent: Literal["chart"]
    chart: ChartSemantic


class MultiColumnSlideDSL(BaseSlideDSL):
    model_config = {"extra": "forbid"}

    intent: Literal["multi_column"]
    columns: List[ColumnBlock] = Field(default_factory=list)


class ArchitectureSlideDSL(BaseSlideDSL):
    model_config = {"extra": "forbid"}

    intent: Literal["architecture"]
    layers: List[ArchitectureLayer] = Field(default_factory=list)


class QuoteSlideDSL(BaseSlideDSL):
    model_config = {"extra": "forbid"}

    intent: Literal["quote"]
    quote: str
    author: Optional[str] = None


class DividerSlideDSL(BaseSlideDSL):
    model_config = {"extra": "forbid"}

    intent: Literal["divider"]
    subtitle: Optional[str] = None


class TeamSlideDSL(BaseSlideDSL):
    model_config = {"extra": "forbid"}

    intent: Literal["team"]
    members: List[TeamMember] = Field(default_factory=list)


SlideDSL = Annotated[
    Union[
        CoverSlideDSL,
        AgendaSlideDSL,
        TextSlideDSL,
        TimelineSlideDSL,
        KpiSlideDSL,
        ComparisonSlideDSL,
        SwotSlideDSL,
        RoadmapSlideDSL,
        ProcessFlowSlideDSL,
        ChartSlideDSL,
        MultiColumnSlideDSL,
        ArchitectureSlideDSL,
        QuoteSlideDSL,
        DividerSlideDSL,
        TeamSlideDSL,
    ],
    Field(discriminator="intent"),
]


class PresentationDSL(BaseModel):
    model_config = {"extra": "forbid"}

    title: str
    audience: str = "通用受众"
    tone: str = "清晰、教学"
    theme: str = "modern_blue"
    slides: List[SlideDSL] = Field(default_factory=list)

