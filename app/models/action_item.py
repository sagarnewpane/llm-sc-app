from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class ActionItem(SQLModel, table=True):
    __tablename__ = "action_items"

    id: str = Field(primary_key=True)
    title: str
    description: Optional[str] = None
    status: str = "open"
    priority: str = "medium"
    source_type: str = "manual"
    source_id: Optional[str] = None
    assignee: Optional[str] = None
    due_hint: Optional[str] = None
    category: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
