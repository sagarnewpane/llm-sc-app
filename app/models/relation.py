from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class Relation(SQLModel, table=True):
    __tablename__ = "relations"

    id: Optional[int] = Field(default=None, primary_key=True)
    source_entity_id: int
    target_entity_id: int
    relation_type: str
    weight: Optional[int] = None
    first_seen_year: Optional[int] = None
    last_seen_year: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
