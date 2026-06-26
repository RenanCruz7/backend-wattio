from fastapi import APIRouter

from app.api.routes.films import router as films_router
from app.api.routes.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(films_router, tags=["films"])
