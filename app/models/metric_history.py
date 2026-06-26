from datetime import date, datetime
from typing import Optional

from sqlalchemy import JSON
from sqlmodel import SQLModel, Field, Column


class MetricHistory(SQLModel, table=True):
    __tablename__ = "metrics_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    snapshot_date: date
    metric_family: str
    metric_key: str
    metric_value: dict = Field(sa_column=Column(JSON))
    run_id: Optional[int] = None
    schema_version: str
    created_at: Optional[datetime] = None
