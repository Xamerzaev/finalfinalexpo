from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Date, Numeric, UniqueConstraint, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="user")  # 'admin', 'user', 'viewer'
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Отношения
    user_projects = relationship("UserProject", back_populates="user", cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Отношения
    cabinets = relationship("Cabinet", back_populates="project", cascade="all, delete-orphan")
    user_projects = relationship("UserProject", back_populates="project", cascade="all, delete-orphan")

class UserProject(Base):
    __tablename__ = "user_projects"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    role = Column(String(50), default="viewer")  # 'owner', 'editor', 'viewer'
    created_at = Column(DateTime, default=func.now())
    
    # Отношения
    user = relationship("User", back_populates="user_projects")
    project = relationship("Project", back_populates="user_projects")

class Cabinet(Base):
    __tablename__ = "cabinets"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    marketplace = Column(String(50), nullable=False)  # 'ozon' или 'wildberries'
    name = Column(String(255), nullable=False)
    api_key = Column(String(255))
    api_secret = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Отношения
    project = relationship("Project", back_populates="cabinets")
    metric_values = relationship("MetricValue", back_populates="cabinet", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="cabinet", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="cabinet", cascade="all, delete-orphan")
    analysis_logs = relationship("AnalysisLog", back_populates="cabinet", cascade="all, delete-orphan")
    uploaded_files = relationship("UploadedFile", back_populates="cabinet", cascade="all, delete-orphan")

class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    
    id = Column(Integer, primary_key=True, index=True)
    cabinet_id = Column(Integer, ForeignKey("cabinets.id", ondelete="CASCADE"))
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # 'metrics', 'report_table'
    upload_date = Column(DateTime, default=func.now())
    processed = Column(Boolean, default=False)
    
    # Отношения
    cabinet = relationship("Cabinet", back_populates="uploaded_files")
    analysis_results = relationship("AnalysisResult", back_populates="uploaded_file", cascade="all, delete-orphan")

class MetricCategory(Base):
    __tablename__ = "metric_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    # Отношения
    metrics = relationship("Metric", back_populates="category")

class Metric(Base):
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category_id = Column(Integer, ForeignKey("metric_categories.id"))
    source = Column(String(100))  # 'api', 'formula', 'manual', 'excel'
    formula = Column(Text)  # Для расчетных метрик
    unit = Column(String(50))  # Единица измерения
    is_key_metric = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Отношения
    category = relationship("MetricCategory", back_populates="metrics")
    values = relationship("MetricValue", back_populates="metric", cascade="all, delete-orphan")
    source_relations = relationship("MetricRelation", foreign_keys="MetricRelation.source_metric_id", back_populates="source_metric", cascade="all, delete-orphan")
    target_relations = relationship("MetricRelation", foreign_keys="MetricRelation.target_metric_id", back_populates="target_metric", cascade="all, delete-orphan")
    change_reasons = relationship("MetricChangeReason", back_populates="metric", cascade="all, delete-orphan")
    action_plans = relationship("MetricActionPlan", back_populates="metric", cascade="all, delete-orphan")

class MetricValue(Base):
    __tablename__ = "metric_values"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(Integer, ForeignKey("metrics.id", ondelete="CASCADE"))
    cabinet_id = Column(Integer, ForeignKey("cabinets.id", ondelete="CASCADE"))
    value = Column(Numeric, nullable=False)
    date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Отношения
    metric = relationship("Metric", back_populates="values")
    cabinet = relationship("Cabinet", back_populates="metric_values")
    
    # Уникальный индекс для предотвращения дублирования
    __table_args__ = (
        UniqueConstraint('metric_id', 'cabinet_id', 'date', name='uix_metric_value'),
        Index('idx_metric_values_date', 'date'),
        Index('idx_metric_values_cabinet_metric', 'cabinet_id', 'metric_id'),
    )

class MetricRelation(Base):
    __tablename__ = "metric_relations"
    
    id = Column(Integer, primary_key=True, index=True)
    source_metric_id = Column(Integer, ForeignKey("metrics.id", ondelete="CASCADE"))
    target_metric_id = Column(Integer, ForeignKey("metrics.id", ondelete="CASCADE"))
    relation_type = Column(String(50), nullable=False)  # 'correlation', 'causation', 'dependency'
    weight = Column(Numeric)  # Сила связи от 0 до 1
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    # Отношения
    source_metric = relationship("Metric", foreign_keys=[source_metric_id], back_populates="source_relations")
    target_metric = relationship("Metric", foreign_keys=[target_metric_id], back_populates="target_relations")
    
    # Уникальный индекс для предотвращения дублирования
    __table_args__ = (
        UniqueConstraint('source_metric_id', 'target_metric_id', 'relation_type', name='uix_metric_relation'),
    )

class MetricChangeReason(Base):
    __tablename__ = "metric_change_reasons"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(Integer, ForeignKey("metrics.id", ondelete="CASCADE"))
    reason = Column(Text, nullable=False)
    direction = Column(String(10), nullable=False)  # 'increase' или 'decrease'
    created_at = Column(DateTime, default=func.now())
    
    # Отношения
    metric = relationship("Metric", back_populates="change_reasons")

class MetricActionPlan(Base):
    __tablename__ = "metric_action_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(Integer, ForeignKey("metrics.id", ondelete="CASCADE"))
    action_description = Column(Text, nullable=False)
    priority = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
    
    # Отношения
    metric = relationship("Metric", back_populates="action_plans")

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    cabinet_id = Column(Integer, ForeignKey("cabinets.id", ondelete="CASCADE"))
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    status = Column(String(50), default="draft")  # 'draft', 'published', 'archived'
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Отношения
    cabinet = relationship("Cabinet", back_populates="reports")
    tasks = relationship("Task", back_populates="report", cascade="all, delete-orphan")
    
    # Индексы
    __table_args__ = (
        Index('idx_reports_cabinet_period', 'cabinet_id', 'period_start', 'period_end'),
    )

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    cabinet_id = Column(Integer, ForeignKey("cabinets.id", ondelete="CASCADE"))
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="new")  # 'new', 'in_progress', 'completed', 'cancelled'
    priority = Column(String(20), default="medium")  # 'low', 'medium', 'high', 'critical'
    due_date = Column(Date)
    external_id = Column(String(100))  # ID в внешней системе задач
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Отношения
    cabinet = relationship("Cabinet", back_populates="tasks")
    report = relationship("Report", back_populates="tasks")
    
    # Индексы
    __table_args__ = (
        Index('idx_tasks_status', 'status'),
        Index('idx_tasks_cabinet_status', 'cabinet_id', 'status'),
    )

class DataSource(Base):
    __tablename__ = "data_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    type = Column(String(50), nullable=False)  # 'api', 'database', 'file', 'manual'
    connection_details = Column(JSON)  # Детали подключения в JSON формате
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class AnalysisLog(Base):
    __tablename__ = "analysis_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    cabinet_id = Column(Integer, ForeignKey("cabinets.id", ondelete="CASCADE"))
    analysis_type = Column(String(100), nullable=False)
    parameters = Column(JSON)
    result_summary = Column(Text)
    status = Column(String(50), nullable=False)  # 'success', 'failure', 'in_progress'
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    
    # Отношения
    cabinet = relationship("Cabinet", back_populates="analysis_logs")

class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    uploaded_file_id = Column(Integer, ForeignKey("uploaded_files.id", ondelete="CASCADE"))
    analysis_type = Column(String(100), nullable=False)  # 'trends', 'competitors', 'metrics'
    result_data = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    
    # Отношения
    uploaded_file = relationship("UploadedFile", back_populates="analysis_results")

class SystemSetting(Base):
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
