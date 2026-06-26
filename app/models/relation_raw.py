from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class RelationRaw(SQLModel, table=True):
    __tablename__ = "relations_raw"

    id: Optional[int] = Field(default=None, primary_key=True)
    review_id: str
    year: Optional[int] = None
    source_node: str
    target_node: str
    relation: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
