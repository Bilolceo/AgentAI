from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class KnowledgeIngest(BaseModel):
    source: str
    language: Optional[str] = None
    content: str  # raw text; the ingest pipeline splits it into chunks


class KnowledgeChunkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: Optional[str]
    language: Optional[str]
    content: str
    created_at: datetime


class KnowledgeItemCreate(BaseModel):
    category: str
    title: str
    content_uz: str
    content_ru: str
    tags: list[str] = []
    is_active: bool = True


class KnowledgeItemUpdate(BaseModel):
    category: Optional[str] = None
    title: Optional[str] = None
    content_uz: Optional[str] = None
    content_ru: Optional[str] = None
    tags: Optional[list[str]] = None
    is_active: Optional[bool] = None


class KnowledgeItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    title: str
    content_uz: str
    content_ru: str
    tags: Optional[list]
    is_active: bool
