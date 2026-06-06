from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class IntentAnalysis(BaseModel):
    model_config = {"extra": "ignore"}

    topic: str = ""
    audience: str = "通用受众"
    goal: str = "教学/汇报"
    tone: str = "清晰、教学"
    preferred_theme: Optional[Literal["modern_blue", "paper_light", "academic_gray", "minimal_black"]] = Field(
        default=None, alias="preferredTheme"
    )
    slide_count: int = Field(default=12, alias="slideCount")


class SlideSkeleton(BaseModel):
    model_config = {"extra": "ignore"}

    id: str
    intent: str
    section: str = ""
    title: str = ""
    purpose: str = ""

    @field_validator("id", mode="before")
    @classmethod
    def _coerce_id(cls, v):
        if v is None:
            return ""
        return str(v)


class PresentationPlan(BaseModel):
    model_config = {"extra": "ignore"}

    title: str = ""
    theme: Optional[str] = None
    slides: List[SlideSkeleton] = Field(default_factory=list)
