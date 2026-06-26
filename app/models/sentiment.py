from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class Sentiment(SQLModel, table=True):
    __tablename__ = "sentiments"

    id: Optional[int] = Field(default=None, primary_key=True)
    aspect: str = Field(unique=True)
    display_aspect: Optional[str] = None
    positive_count: Optional[int] = None
    neutral_count: Optional[int] = None
    negative_count: Optional[int] = None
    mention_count: Optional[int] = None
    avg_sentiment_score: Optional[float] = None
    first_seen_year: Optional[int] = None
    last_seen_year: Optional[int] = None
    updated_at: Optional[datetime] = None
