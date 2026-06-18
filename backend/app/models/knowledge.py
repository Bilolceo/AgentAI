from __future__ import annotations

from datetime import datetime
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.core.db import Base


class KnowledgeChunk(Base):
    """RAG knowledge-base chunk + optional embedding (pgvector)."""

    __tablename__ = "knowledge_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[Optional[str]] = mapped_column(String(255))  # document name / URL
    language: Mapped[Optional[str]] = mapped_column(String(8))
    content: Mapped[str] = mapped_column(Text)
    # Nullable: MVP keyword search works without embeddings; pgvector path fills
    # this in once an embedding provider is configured.
    embedding: Mapped[Optional[list[float]]] = mapped_column(
        Vector(settings.embedding_dim), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
