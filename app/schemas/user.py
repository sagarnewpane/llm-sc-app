from typing import Any, Optional

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: str
    email: str
    is_active: bool = True
    created_at: Optional[str] = None
    app_metadata: Optional[dict[str, Any]] = None
    user_metadata: Optional[dict[str, Any]] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    expires_at: Optional[int] = None
    user: Optional[UserRead] = None


class RefreshRequest(BaseModel):
    refresh_token: str


class SessionInfo(BaseModel):
    access_token: str
    refresh_token: str
    user: Optional[UserRead] = None
