from datetime import datetime
from typing import Optional

from sqlalchemy import JSON
from sqlmodel import SQLModel, Field, Column


class MetricCurrent(SQLModel, table=True):
    __tablename__ = "metrics_current"

    id: Optional[int] = Field(default=None, primary_key=True)
    metric_family: str
    metric_key: str
    metric_value: dict = Field(sa_column=Column(JSON))
    computed_at: datetime
    run_id: Optional[int] = None
    schema_version: str
