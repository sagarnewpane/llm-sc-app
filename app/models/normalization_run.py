from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class NormalizationRun(SQLModel, table=True):
    __tablename__ = "normalization_runs"

    id: Optional[int] = Field(default=None, primary_key=True)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    status: str
    entities_processed: Optional[int] = None
    relations_processed: Optional[int] = None
    sentiments_processed: Optional[int] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
