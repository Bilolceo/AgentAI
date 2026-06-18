from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BookingCreate(BaseModel):
    service: str
    scheduled_at: Optional[datetime] = None
    customer_id: Optional[int] = None
    call_id: Optional[int] = None
    notes: Optional[str] = None


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service: str
    scheduled_at: Optional[datetime]
    status: str
    notes: Optional[str]
    created_at: datetime
