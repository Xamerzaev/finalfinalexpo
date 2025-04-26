from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.core.config import settings
from app.api import api_router
from app.db.session import engine
from app.db.base import Base
from app.models import models

# Создаем таблицы в базе данных
Base.metadata.create_all(bind=engine)

# Создаем директорию для загрузки файлов, если она не существует
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # или ["http://localhost:3000"] — безопаснее
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем API роутеры
app.include_router(api_router, prefix=settings.API_V1_STR)

# Монтируем директорию для загруженных файлов
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_FOLDER), name="uploads")

@app.get("/")
def root():
    """
    Корневой эндпоинт для проверки работоспособности API.
    """
    return {
        "message": "Добро пожаловать в API системы аналитики данных маркетплейсов",
        "status": "online",
        "version": settings.PROJECT_VERSION,
        "docs": f"{settings.API_V1_STR}/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
