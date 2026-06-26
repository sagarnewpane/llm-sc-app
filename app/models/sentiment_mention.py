from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class SentimentMention(SQLModel, table=True):
    __tablename__ = "sentiment_mentions"

    id: Optional[int] = Field(default=None, primary_key=True)
    sentiment_id: int
    review_id: str
    raw_sentiment_id: int = Field(unique=True)
    aspect_raw: Optional[str] = None
    sentiment_label: Optional[str] = None
    sentiment_score: Optional[float] = None
    evidence: Optional[str] = None
    updated_at: Optional[datetime] = None
