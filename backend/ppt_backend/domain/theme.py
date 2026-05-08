from __future__ import annotations

from typing import Dict, Optional

from pydantic import BaseModel, Field


class ThemeColors(BaseModel):
    model_config = {"extra": "forbid"}

    background: str
    surface: str
    text: str
    muted: str
    primary: str
    secondary: str
    border: str


class ThemeTypography(BaseModel):
    model_config = {"extra": "forbid"}

    font_family: str = Field(alias="fontFamily")
    title_pt: int = Field(alias="titlePt")
    subtitle_pt: int = Field(alias="subtitlePt")
    body_pt: int = Field(alias="bodyPt")
    small_pt: int = Field(alias="smallPt")


class ThemeSpacing(BaseModel):
    model_config = {"extra": "forbid"}

    slide_padding_px: int = Field(alias="slidePaddingPx")
    gap_px: int = Field(alias="gapPx")


class ThemeTokens(BaseModel):
    model_config = {"extra": "forbid"}

    name: str
    colors: ThemeColors
    typography: ThemeTypography
    spacing: ThemeSpacing


DEFAULT_THEMES: Dict[str, ThemeTokens] = {
    "modern_blue": ThemeTokens(
        name="Modern Blue",
        colors={
            "background": "#0B1220",
            "surface": "#111B2E",
            "text": "#E6EEF9",
            "muted": "#A9B7D0",
            "primary": "#0078D4",
            "secondary": "#2B88D8",
            "border": "rgba(255,255,255,0.12)",
        },
        typography={
            "fontFamily": "ui-sans-serif, system-ui, Segoe UI, Arial",
            "titlePt": 36,
            "subtitlePt": 20,
            "bodyPt": 16,
            "smallPt": 12,
        },
        spacing={"slidePaddingPx": 56, "gapPx": 18},
    ),
    "paper_light": ThemeTokens(
        name="Paper Light",
        colors={
            "background": "#F7F4EE",
            "surface": "#FFFFFF",
            "text": "#121826",
            "muted": "#4B5563",
            "primary": "#0EA5E9",
            "secondary": "#6366F1",
            "border": "rgba(17,24,39,0.12)",
        },
        typography={
            "fontFamily": "ui-sans-serif, system-ui, Segoe UI, Arial",
            "titlePt": 36,
            "subtitlePt": 20,
            "bodyPt": 16,
            "smallPt": 12,
        },
        spacing={"slidePaddingPx": 56, "gapPx": 18},
    ),
    "academic_gray": ThemeTokens(
        name="Academic Gray",
        colors={
            "background": "#FFFFFF",
            "surface": "#F3F4F6",
            "text": "#111827",
            "muted": "#4B5563",
            "primary": "#374151",
            "secondary": "#6B7280",
            "border": "rgba(17,24,39,0.10)",
        },
        typography={
            "fontFamily": "Times New Roman, Georgia, serif",
            "titlePt": 34,
            "subtitlePt": 18,
            "bodyPt": 16,
            "smallPt": 12,
        },
        spacing={"slidePaddingPx": 64, "gapPx": 16},
    ),
    "minimal_black": ThemeTokens(
        name="Minimal Black",
        colors={
            "background": "#0A0A0A",
            "surface": "#111111",
            "text": "#FAFAFA",
            "muted": "#A3A3A3",
            "primary": "#FFFFFF",
            "secondary": "#D4D4D4",
            "border": "rgba(255,255,255,0.10)",
        },
        typography={
            "fontFamily": "ui-sans-serif, system-ui, Segoe UI, Arial",
            "titlePt": 38,
            "subtitlePt": 20,
            "bodyPt": 16,
            "smallPt": 12,
        },
        spacing={"slidePaddingPx": 60, "gapPx": 20},
    ),
}


def get_theme_tokens(theme_name: Optional[str]) -> ThemeTokens:
    if not theme_name:
        return DEFAULT_THEMES["modern_blue"]
    return DEFAULT_THEMES.get(theme_name) or DEFAULT_THEMES["modern_blue"]

