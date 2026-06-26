from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class EntityRaw(SQLModel, table=True):
    __tablename__ = "entities_raw"

    id: Optional[int] = Field(default=None, primary_key=True)
    review_id: str
    year: Optional[int] = None
    period: Optional[str] = None
    trip_type: Optional[str] = None
    entity_name: str
    entity_type: str
    quote: Optional[str] = None
    rating: Optional[float] = None
    created_at: Optional[datetime] = None
