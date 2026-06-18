from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    phone_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    preferred_language: Mapped[Optional[str]] = mapped_column(String(8))  # uz-UZ / ru-RU
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
