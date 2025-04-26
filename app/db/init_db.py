from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import logging
from dotenv import load_dotenv
from passlib.context import CryptContext

from app.db.base import Base
from app.models.models import User, Project, Cabinet, UploadedFile, MetricCategory, Metric
from app.models.models import MetricValue, MetricRelation, MetricChangeReason, MetricActionPlan
from app.models.models import Report, Task, UserProject, DataSource, AnalysisLog, AnalysisResult, SystemSetting
from app.core.config import settings

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

# Настройка хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_db():
    """
    Инициализация базы данных: создание таблиц и базовых данных
    """
    try:
        # Создаем директорию для базы данных, если она не существует
        db_dir = os.path.dirname(settings.DATABASE_URL.replace('sqlite:///', ''))
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        # Создаем директорию для загрузки файлов, если она не существует
        os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
        
        # Создаем движок SQLAlchemy
        engine = create_engine(
            settings.DATABASE_URL, 
            connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
        )
        
        # Создаем все таблицы в базе данных
        Base.metadata.create_all(bind=engine)
        
        # Создаем сессию
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Создаем базового пользователя, если его нет
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            # Генерируем хеш пароля "admin"
            hashed_password = pwd_context.hash("admin")
            admin_user = User(
                username="admin",
                email="admin@example.com",
                password_hash=hashed_password,
                role="admin"
            )
            db.add(admin_user)
            db.commit()
            logger.info(f"Created admin user with password hash: {hashed_password}")
        else:
            # Обновляем пароль существующего пользователя admin
            hashed_password = pwd_context.hash("admin")
            admin_user.password_hash = hashed_password
            db.commit()
            logger.info(f"Updated admin user password hash: {hashed_password}")
        
        # Создаем базовые категории метрик, если их нет
        if db.query(MetricCategory).count() == 0:
            categories = [
                MetricCategory(name="Продажи", description="Метрики, связанные с продажами"),
                MetricCategory(name="Трафик", description="Метрики, связанные с трафиком"),
                MetricCategory(name="Конверсия", description="Метрики, связанные с конверсией"),
                MetricCategory(name="Финансы", description="Финансовые метрики"),
                MetricCategory(name="Склад", description="Метрики, связанные со складом"),
                MetricCategory(name="Маркетинг", description="Маркетинговые метрики"),
                MetricCategory(name="Клиенты", description="Метрики, связанные с клиентами"),
                MetricCategory(name="Другое", description="Прочие метрики")
            ]
            db.add_all(categories)
            db.commit()
            logger.info("Created basic metric categories")
        
        # Создаем базовые метрики, если их нет
        if db.query(Metric).count() == 0:
            sales_category = db.query(MetricCategory).filter(MetricCategory.name == "Продажи").first()
            traffic_category = db.query(MetricCategory).filter(MetricCategory.name == "Трафик").first()
            conversion_category = db.query(MetricCategory).filter(MetricCategory.name == "Конверсия").first()
            finance_category = db.query(MetricCategory).filter(MetricCategory.name == "Финансы").first()
            
            metrics = [
                Metric(
                    name="Выручка", 
                    description="Общая выручка от продаж", 
                    category_id=sales_category.id,
                    source="excel",
                    unit="руб.",
                    is_key_metric=True
                ),
                Metric(
                    name="Количество заказов", 
                    description="Общее количество заказов", 
                    category_id=sales_category.id,
                    source="excel",
                    unit="шт.",
                    is_key_metric=True
                ),
                Metric(
                    name="Средний чек", 
                    description="Средняя сумма заказа", 
                    category_id=sales_category.id,
                    source="formula",
                    formula="Выручка / Количество заказов",
                    unit="руб.",
                    is_key_metric=True
                ),
                Metric(
                    name="Просмотры", 
                    description="Количество просмотров товаров", 
                    category_id=traffic_category.id,
                    source="excel",
                    unit="шт.",
                    is_key_metric=True
                ),
                Metric(
                    name="Конверсия в заказ", 
                    description="Отношение количества заказов к количеству просмотров", 
                    category_id=conversion_category.id,
                    source="formula",
                    formula="Количество заказов / Просмотры * 100",
                    unit="%",
                    is_key_metric=True
                ),
                Metric(
                    name="Прибыль", 
                    description="Чистая прибыль", 
                    category_id=finance_category.id,
                    source="excel",
                    unit="руб.",
                    is_key_metric=True
                )
            ]
            db.add_all(metrics)
            db.commit()
            logger.info("Created basic metrics")
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

if __name__ == "__main__":
    init_db()
