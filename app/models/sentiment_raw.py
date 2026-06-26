from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class SentimentRaw(SQLModel, table=True):
    __tablename__ = "sentiments_raw"

    id: Optional[int] = Field(default=None, primary_key=True)
    review_id: str
    year: Optional[int] = None
    trip_type: Optional[str] = None
    aspect: str
    sentiment: str
    score: float
    evidence: Optional[str] = None
    rating: Optional[float] = None
    created_at: Optional[datetime] = None
