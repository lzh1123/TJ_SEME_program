from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from .theme import ThemeTokens


ComponentType = Literal[
    "Title",
    "Subtitle",
    "Text",
    "BulletList",
    "Quote",
    "Divider",
    "Image",
    "Timeline",
    "KpiCards",
    "ComparisonTable",
    "Swot",
    "Roadmap",
    "ProcessFlow",
    "Chart",
    "MultiColumn",
    "TeamCards",
    "Statistics",
    "ArchitectureDiagram",
]


class StyleSpec(BaseModel):
    model_config = {"extra": "forbid"}

    color: Optional[str] = None
    background: Optional[str] = None
    border_color: Optional[str] = Field(default=None, alias="borderColor")
    border_width: Optional[int] = Field(default=None, alias="borderWidth")
    radius: Optional[int] = None
    font_family: Optional[str] = Field(default=None, alias="fontFamily")
    font_size: Optional[int] = Field(default=None, alias="fontSize")
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    align: Optional[Literal["left", "center", "right"]] = None


class EditableSpec(BaseModel):
    model_config = {"extra": "forbid"}

    movable: bool = True
    resizable: bool = True
    rotatable: bool = False
    editable_props: List[str] = Field(default_factory=list, alias="editableProps")


class ComponentSpec(BaseModel):
    model_config = {"extra": "forbid"}

    id: str
    type: ComponentType
    x: float
    y: float
    w: float
    h: float
    z: int = 0
    rotation: float = 0
    style: StyleSpec = Field(default_factory=StyleSpec)
    props: Dict[str, Any] = Field(default_factory=dict)
    editable: EditableSpec = Field(default_factory=EditableSpec)


class RenderSlide(BaseModel):
    model_config = {"extra": "forbid"}

    id: str
    width: int = 1280
    height: int = 720
    background: Optional[str] = None
    components: List[ComponentSpec] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class RenderTree(BaseModel):
    model_config = {"extra": "forbid"}

    presentation_id: str = Field(alias="presentationId")
    title: str
    theme_name: str = Field(alias="themeName")
    theme_tokens: ThemeTokens = Field(alias="themeTokens")
    slides: List[RenderSlide] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class ComponentPatch(BaseModel):
    model_config = {"extra": "forbid"}

    x: Optional[float] = None
    y: Optional[float] = None
    w: Optional[float] = None
    h: Optional[float] = None
    z: Optional[int] = None
    rotation: Optional[float] = None
    style: Optional[StyleSpec] = None
    props: Optional[Dict[str, Any]] = None

