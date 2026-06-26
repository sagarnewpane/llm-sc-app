from datetime import datetime
from typing import Optional

from sqlalchemy import JSON
from sqlmodel import SQLModel, Field, Column


class EntityRanking(SQLModel, table=True):
    __tablename__ = "entity_rankings"

    id: Optional[int] = Field(default=None, primary_key=True)
    ranking_type: str
    entity_id: int
    canonical_name: str
    display_name: str
    entity_type: str
    rank_position: int
    score: float
    is_sacred: bool
    metadata_: Optional[dict] = Field(default=None, sa_column=Column("metadata", JSON))
    computed_at: datetime
    run_id: Optional[int] = None
