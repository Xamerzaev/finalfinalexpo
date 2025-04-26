from fastapi import APIRouter

from app.api.endpoints import auth, projects, cabinets, file_upload, ai_analytics, reports, tasks, analytics

api_router = APIRouter()

# Подключаем все эндпоинты
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(cabinets.router, prefix="/cabinets", tags=["cabinets"])
api_router.include_router(file_upload.router, prefix="/files", tags=["files"])
api_router.include_router(ai_analytics.router, prefix="/analytics/ai", tags=["ai_analytics"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
