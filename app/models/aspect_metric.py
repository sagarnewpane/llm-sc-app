from datetime import datetime
from typing import Optional

from sqlalchemy import JSON
from sqlmodel import SQLModel, Field, Column


class AspectMetric(SQLModel, table=True):
    __tablename__ = "aspect_metrics"

    id: Optional[int] = Field(default=None, primary_key=True)
    aspect: str = Field(unique=True)
    display_aspect: str
    mention_count: int
    positive_pct: float
    negative_pct: float
    neutral_pct: float
    avg_sentiment_score: Optional[float] = None
    trend_by_year: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    trend_by_period: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    by_trip_type: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    by_reviewer_type: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    computed_at: datetime
    run_id: Optional[int] = None
