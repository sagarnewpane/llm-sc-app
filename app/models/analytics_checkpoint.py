from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class AnalyticsCheckpoint(SQLModel, table=True):
    __tablename__ = "analytics_checkpoints"

    metric_family: str = Field(primary_key=True)
    last_computed_at: datetime
    data_watermark: datetime
    last_run_id: Optional[int] = None
    rows_affected: Optional[int] = None
    updated_at: Optional[datetime] = None
