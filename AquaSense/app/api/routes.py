from fastapi import APIRouter
from app.api.endpoints import fish
from configz import settings

# Create API router
router = APIRouter(prefix=settings.API_V1_STR)

# Include endpoints routers
router.include_router(fish.router, prefix="/fish", tags=["fish"])