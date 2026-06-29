from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class IntentAnalysis(BaseModel):
    model_config = {"extra": "ignore", "populate_by_name": True}

    topic: str = ""
    audience: str = "通用受众"
    goal: str = "教学/汇报"
    tone: str = "清晰、专业、教学友好"
    preferred_theme: Optional[Literal["modern_blue", "paper_light", "academic_gray", "minimal_black"]] = Field(
        default=None, alias="preferredTheme"
    )
    slide_count: int = Field(default=12, alias="slideCount")

    @field_validator("preferred_theme", mode="before")
    @classmethod
    def _normalize_preferred_theme(cls, v):
        if v is None:
            return None
        text = str(v).strip().lower()
        if not text or text in {"none", "null", "default"}:
            return None
        if text in {"modern_blue", "paper_light", "academic_gray", "minimal_black"}:
            return text
        compact = text.replace("-", "_").replace(" ", "_")
        if compact in {"modern_blue", "paper_light", "academic_gray", "minimal_black"}:
            return compact
        if any(key in text for key in ("blue", "科技", "现代", "商务", "tech", "modern")):
            return "modern_blue"
        if any(key in text for key in ("paper", "light", "简洁", "清新", "白", "浅")):
            return "paper_light"
        if any(key in text for key in ("academic", "gray", "grey", "学术", "论文", "灰")):
            return "academic_gray"
        if any(key in text for key in ("black", "minimal", "极简", "深色", "黑")):
            return "minimal_black"
        return None

    @field_validator("slide_count", mode="before")
    @classmethod
    def _coerce_slide_count(cls, v):
        try:
            n = int(v)
        except Exception:
            return 12
        return max(6, min(30, n))


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
