from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.db.supabase_client import get_supabase

security = HTTPBearer()


def _user_from_supabase(supabase_user: Any) -> dict[str, Any]:
    return {
        "id": supabase_user.id,
        "email": supabase_user.email,
        "is_active": True,
        "created_at": str(supabase_user.created_at) if supabase_user.created_at else None,
        "app_metadata": supabase_user.app_metadata if hasattr(supabase_user, "app_metadata") else {},
        "user_metadata": supabase_user.user_metadata if hasattr(supabase_user, "user_metadata") else {},
    }


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    token = credentials.credentials
    sb = get_supabase()

    try:
        response = sb.auth.get_user(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not response or not response.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return _user_from_supabase(response.user)


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
) -> dict[str, Any] | None:
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
