from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class Entity(SQLModel, table=True):
    __tablename__ = "entities"

    id: Optional[int] = Field(default=None, primary_key=True)
    canonical_name: str
    display_name: str
    entity_type: str
    mention_count: Optional[int] = None
    first_seen_year: Optional[int] = None
    last_seen_year: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
