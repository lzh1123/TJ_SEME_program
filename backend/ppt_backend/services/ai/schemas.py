from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class IntentAnalysis(BaseModel):
    model_config = {"extra": "forbid"}

    topic: str
    audience: str = "通用受众"
    goal: str = "教学/汇报"
    tone: str = "清晰、教学"
    preferred_theme: Optional[Literal["modern_blue", "paper_light", "academic_gray", "minimal_black"]] = Field(
        default=None, alias="preferredTheme"
    )
    slide_count: int = Field(default=8, alias="slideCount")


class SlideSkeleton(BaseModel):
    model_config = {"extra": "forbid"}

    id: str
    intent: str
    section: str = ""
    title: str
    purpose: str


class PresentationPlan(BaseModel):
    model_config = {"extra": "forbid"}

    title: str
    theme: Optional[str] = None
    slides: List[SlideSkeleton] = Field(default_factory=list)

