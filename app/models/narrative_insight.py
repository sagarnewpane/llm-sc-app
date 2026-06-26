from datetime import datetime
from typing import Optional

from sqlalchemy import JSON
from sqlmodel import SQLModel, Field, Column


class NarrativeInsight(SQLModel, table=True):
    __tablename__ = "narrative_insights"

    id: Optional[int] = Field(default=None, primary_key=True)
    category: str
    priority: str
    title: str
    narrative: str
    evidence: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    recommended_actions: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    audience: str
    computed_at: datetime
    run_id: Optional[int] = None
    is_active: bool
