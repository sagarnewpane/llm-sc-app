from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel


class HealthStatus(BaseModel):
    status: Literal["ok"]


router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthStatus)
def health_check() -> HealthStatus:
    """Provide a lightweight health indicator."""
    return HealthStatus(status="ok")
