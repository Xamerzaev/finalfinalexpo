from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
from typing import List

# Загружаем переменные окружения
load_dotenv()

class Settings(BaseSettings):
    # Основные настройки приложения
    PROJECT_NAME: str = "AI Analytics Assistant"
    PROJECT_DESCRIPTION: str = "Система аналитики данных маркетплейсов с использованием ИИ"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Настройки сервера
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Настройки безопасности
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    
    # Настройки CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Настройки базы данных
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./ai_analytics.db")
    
    # Настройки OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4-1106-preview")
    
    # Настройки файлов
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "./uploads")
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50 MB
    
    # Настройки для демо-данных
    USE_SAMPLE_DATA: bool = os.getenv("USE_SAMPLE_DATA", "False").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Разрешаем дополнительные поля в .env файле

settings = Settings()

# Выводим информацию о пути к папке загрузок
import logging
logging.info(f"Upload folder path: {settings.UPLOAD_FOLDER}")
