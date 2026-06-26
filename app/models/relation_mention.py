from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class RelationMention(SQLModel, table=True):
    __tablename__ = "relation_mentions"

    id: Optional[int] = Field(default=None, primary_key=True)
    relation_id: int
    review_id: str
    raw_relation_id: int = Field(unique=True)
    source_node_raw: Optional[str] = None
    target_node_raw: Optional[str] = None
    relation_type_raw: Optional[str] = None
    description: Optional[str] = None
    updated_at: Optional[datetime] = None
