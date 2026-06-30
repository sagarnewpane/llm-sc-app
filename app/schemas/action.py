from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ActionCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[str] = "open"
    priority: Optional[str] = "medium"
    source_type: Optional[str] = "manual"
    source_id: Optional[str] = None
    assignee: Optional[str] = None
    due_hint: Optional[str] = None
    category: Optional[str] = None


class ActionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    assignee: Optional[str] = None
    due_hint: Optional[str] = None
    category: Optional[str] = None


class ActionResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    source_type: str
    source_id: Optional[str] = None
    assignee: Optional[str] = None
    due_hint: Optional[str] = None
    category: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ActionListResponse(BaseModel):
    actions: list[ActionResponse]
    total: int
