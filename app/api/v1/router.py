from fastapi import APIRouter

from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.health import router as health_router
from app.api.v1.routers.dashboard import router as dashboard_router
from app.api.v1.routers.reviews import router as reviews_router
from app.api.v1.routers.ai_insights import router as ai_router
from app.api.v1.routers.analytics import router as analytics_router
from app.api.v1.routers.heritage import router as heritage_router
from app.api.v1.routers.actions import router as actions_router
from app.core.config import get_settings

settings = get_settings()

router = APIRouter(prefix=settings.api_version_prefix)
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(dashboard_router)
router.include_router(reviews_router)
router.include_router(ai_router)
router.include_router(analytics_router)
router.include_router(heritage_router)
router.include_router(actions_router)
