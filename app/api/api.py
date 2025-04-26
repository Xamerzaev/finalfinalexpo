from fastapi import APIRouter

from app.api.endpoints import analytics, ai_analytics, extended_analytics

api_router = APIRouter()
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(ai_analytics.router, prefix="/ai-analytics", tags=["ai-analytics"])
api_router.include_router(extended_analytics.router, prefix="/extended-analytics", tags=["extended-analytics"])
