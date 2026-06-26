from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class EntityMention(SQLModel, table=True):
    __tablename__ = "entity_mentions"

    id: Optional[int] = Field(default=None, primary_key=True)
    entity_id: int
    review_id: str
    raw_entity_id: int = Field(unique=True)
    entity_name_raw: Optional[str] = None
    normalized_alias: Optional[str] = None
    entity_type_raw: Optional[str] = None
    quote: Optional[str] = None
    updated_at: Optional[datetime] = None
