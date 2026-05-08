from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from .dsl import PresentationDSL
from .render_tree import RenderTree


class PresentationMeta(BaseModel):
    model_config = {"extra": "forbid"}

    id: str
    topic: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), alias="createdAt")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), alias="updatedAt")
    version: int = 1
    extra: Dict[str, Any] = Field(default_factory=dict)


class PresentationBundle(BaseModel):
    model_config = {"extra": "forbid"}

    meta: PresentationMeta
    dsl: PresentationDSL
    render_tree: RenderTree = Field(alias="renderTree")
    last_export_pptx: Optional[str] = Field(default=None, alias="lastExportPptx")

