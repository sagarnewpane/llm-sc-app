from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class ExtractionCheckpoint(SQLModel, table=True):
    __tablename__ = "extraction_checkpoint"

    id: Optional[int] = Field(default=None, primary_key=True)
    review_id: str = Field(unique=True)
    status: str
    error_msg: Optional[str] = None
    attempt_count: Optional[int] = None
    last_attempt_time: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
