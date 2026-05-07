from fastapi import APIRouter

from app.api.v1.endpoints import health
from app.api.v1 import uploads, analyses

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
api_router.include_router(analyses.router, prefix="/analyses", tags=["analyses"])
