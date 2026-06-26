from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, ARRAY
from sqlmodel import SQLModel, Field, Column


class AnalyticsRun(SQLModel, table=True):
    __tablename__ = "analytics_runs"

    id: Optional[int] = Field(default=None, primary_key=True)
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str
    trigger_type: str
    families_computed: Optional[list] = Field(default=None, sa_column=Column(ARRAY(JSON)))
    families_skipped: Optional[list] = Field(default=None, sa_column=Column(ARRAY(JSON)))
    data_watermark: Optional[datetime] = None
    review_count: Optional[int] = None
    entity_count: Optional[int] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    metadata_: Optional[dict] = Field(default=None, sa_column=Column("metadata", JSON))
    created_at: Optional[datetime] = None
