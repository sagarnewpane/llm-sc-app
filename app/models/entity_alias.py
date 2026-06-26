from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class EntityAlias(SQLModel, table=True):
    __tablename__ = "entity_aliases"

    id: Optional[int] = Field(default=None, primary_key=True)
    entity_id: int
    normalized_alias: str
    display_alias: Optional[str] = None
    entity_type: str
    confidence: Optional[float] = None
    mention_count: Optional[int] = None
    status: str
    source: Optional[str] = None
    match_method: Optional[str] = None
    suggested_merge_entity_id: Optional[int] = None
    scope_type: Optional[str] = None
    scope_id: Optional[str] = None
    first_seen_raw_id: Optional[int] = None
    last_seen_raw_id: Optional[int] = None
    updated_at: Optional[datetime] = None
