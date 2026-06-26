from typing import Optional

from sqlalchemy import JSON
from sqlmodel import SQLModel, Field, Column


class VizMetadata(SQLModel, table=True):
    __tablename__ = "viz_metadata"

    id: Optional[int] = Field(default=None, primary_key=True)
    metric_family: str
    metric_key: str
    chart_type: str
    title: str
    description: Optional[str] = None
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    color_scheme: Optional[str] = None
    sort_order: Optional[int] = None
    dashboard_section: str
    config: Optional[dict] = Field(default=None, sa_column=Column(JSON))
