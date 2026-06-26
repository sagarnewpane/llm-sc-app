from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.db.supabase_client import get_supabase
from app.dependencies import get_current_user
from app.schemas.user import RefreshRequest, TokenResponse, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_response(user: Any) -> UserRead:
    return UserRead(
        id=user.id,
        email=user.email or "",
        is_active=True,
        created_at=str(user.created_at) if user.created_at else None,
        app_metadata=user.app_metadata if hasattr(user, "app_metadata") else {},
        user_metadata=user.user_metadata if hasattr(user, "user_metadata") else {},
    )


def _token_response(session: Any) -> TokenResponse:
    return TokenResponse(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        token_type="bearer",
        expires_in=session.expires_in or 3600,
        expires_at=session.expires_at,
        user=_user_response(session.user) if session.user else None,
    )


@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def signup(user_create: UserCreate) -> TokenResponse:
    sb = get_supabase()

    try:
        result = sb.auth.sign_up(
            email=user_create.email,
            password=user_create.password,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not result.session:
        raise HTTPException(
            status_code=status.HTTP_201_CREATED,
            detail="User created. Check your email for confirmation.",
        )

    return _token_response(result.session)


@router.post("/login", response_model=TokenResponse)
async def login(user_create: UserCreate) -> TokenResponse:
    sb = get_supabase()

    try:
        result = sb.auth.sign_in_with_password(
            email=user_create.email,
            password=user_create.password,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not result.session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return _token_response(result.session)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh: RefreshRequest) -> TokenResponse:
    sb = get_supabase()

    try:
        result = sb.auth.refresh_session(refresh.refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if not result.session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh session",
        )

    return _token_response(result.session)


@router.get("/me", response_model=UserRead)
async def read_current_user(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> UserRead:
    return UserRead(**current_user)


@router.post("/logout")
async def logout(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, str]:
    sb = get_supabase()
    try:
        sb.auth.sign_out()
    except Exception:
        pass
    return {"message": "Logged out successfully"}
