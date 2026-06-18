from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class KnowledgeItem(Base):
    """Structured clinic knowledge-base item (bilingual, categorised).

    Deterministic keyword/category/tag search (no embeddings yet).
    """

    __tablename__ = "knowledge_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(48), index=True)
    title: Mapped[str] = mapped_column(String(255))
    content_uz: Mapped[str] = mapped_column(Text)
    content_ru: Mapped[str] = mapped_column(Text)
    tags: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
