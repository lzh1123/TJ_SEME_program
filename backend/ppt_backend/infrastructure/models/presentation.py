from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Presentation(Base):
    __tablename__ = "presentations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    topic: Mapped[Optional[str]] = mapped_column(String(500), default=None)
    theme: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    bundle_path: Mapped[Optional[str]] = mapped_column(String(500), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None
    )

    def __repr__(self) -> str:
        return f"<Presentation(id={self.id}, title={self.title})>"
