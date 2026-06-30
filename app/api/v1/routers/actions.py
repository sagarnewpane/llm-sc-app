from __future__ import annotations

from datetime import datetime
from typing import Optional
import uuid

from fastapi import APIRouter, HTTPException, Query

from app.db.supabase_client import get_supabase
from app.schemas.action import (
    ActionCreate,
    ActionListResponse,
    ActionResponse,
    ActionUpdate,
)

router = APIRouter(prefix="/actions", tags=["actions"])


def _to_response(data: dict) -> ActionResponse:
    return ActionResponse(
        id=data["id"],
        title=data["title"],
        description=data.get("description"),
        status=data.get("status", "open"),
        priority=data.get("priority", "medium"),
        source_type=data.get("source_type", "manual"),
        source_id=data.get("source_id"),
        assignee=data.get("assignee"),
        due_hint=data.get("due_hint"),
        category=data.get("category"),
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


@router.get("/", response_model=ActionListResponse)
async def list_actions(
    status: Optional[str] = Query(None),
    source_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
) -> ActionListResponse:
    sb = get_supabase()

    query = sb.table("action_items").select("*")
    if status:
        query = query.eq("status", status)
    if source_type:
        query = query.eq("source_type", source_type)

    result = query.order("created_at", desc=True).limit(limit).execute()
    items = [_to_response(d) for d in (result.data or [])]

    return ActionListResponse(actions=items, total=len(items))


@router.post("/", response_model=ActionResponse, status_code=201)
async def create_action(action: ActionCreate) -> ActionResponse:
    sb = get_supabase()

    now = datetime.utcnow().isoformat()
    action_id = "act_" + uuid.uuid4().hex[:12]

    row = {
        "id": action_id,
        "title": action.title,
        "description": action.description,
        "status": action.status or "open",
        "priority": action.priority or "medium",
        "source_type": action.source_type or "manual",
        "source_id": action.source_id,
        "assignee": action.assignee,
        "due_hint": action.due_hint,
        "category": action.category,
        "created_at": now,
        "updated_at": now,
    }

    result = sb.table("action_items").insert(row).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create action")

    return _to_response(result.data[0])


@router.patch("/{action_id}", response_model=ActionResponse)
async def update_action(action_id: str, update: ActionUpdate) -> ActionResponse:
    sb = get_supabase()

    existing = sb.table("action_items").select("*").eq("id", action_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Action not found")

    updates = {k: v for k, v in update.model_dump(exclude_unset=True).items()}
    if not updates:
        return _to_response(existing.data[0])

    updates["updated_at"] = datetime.utcnow().isoformat()

    result = sb.table("action_items").update(updates).eq("id", action_id).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to update action")

    return _to_response(result.data[0])


@router.delete("/{action_id}", status_code=204)
async def delete_action(action_id: str) -> None:
    sb = get_supabase()

    existing = sb.table("action_items").select("*").eq("id", action_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Action not found")

    sb.table("action_items").delete().eq("id", action_id).execute()
