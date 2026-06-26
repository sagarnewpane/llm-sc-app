from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class NormalizationCheckpoint(SQLModel, table=True):
    __tablename__ = "normalization_checkpoints"

    id: Optional[int] = Field(default=None, primary_key=True)
    raw_table: str
    raw_id: int
    run_id: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
