from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date

# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class UserInDB(UserBase):
    id: int
    role: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class User(UserInDB):
    pass

# Project schemas
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ProjectInDB(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Project(ProjectInDB):
    pass

# Cabinet schemas
class CabinetBase(BaseModel):
    name: str
    marketplace: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None

class CabinetCreate(CabinetBase):
    project_id: int

class CabinetUpdate(BaseModel):
    name: Optional[str] = None
    marketplace: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None

class CabinetInDB(CabinetBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Cabinet(CabinetInDB):
    pass

# File upload schemas
class UploadedFileBase(BaseModel):
    original_filename: str
    file_type: str

class UploadedFileCreate(UploadedFileBase):
    cabinet_id: int
    file_path: str

class UploadedFileInDB(UploadedFileBase):
    id: int
    cabinet_id: int
    file_path: str
    upload_date: datetime
    processed: bool

    class Config:
        from_attributes = True

class UploadedFile(UploadedFileInDB):
    pass

# Metric schemas
class MetricBase(BaseModel):
    name: str
    description: Optional[str] = None
    source: Optional[str] = None
    formula: Optional[str] = None
    unit: Optional[str] = None
    is_key_metric: bool = False

class MetricCreate(MetricBase):
    category_id: Optional[int] = None

class MetricUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    source: Optional[str] = None
    formula: Optional[str] = None
    unit: Optional[str] = None
    is_key_metric: Optional[bool] = None

class MetricInDB(MetricBase):
    id: int
    category_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Metric(MetricInDB):
    pass

# Metric value schemas
class MetricValueBase(BaseModel):
    value: float
    date: date

class MetricValueCreate(MetricValueBase):
    metric_id: int
    cabinet_id: int

class MetricValueInDB(MetricValueBase):
    id: int
    metric_id: int
    cabinet_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class MetricValue(MetricValueInDB):
    pass

# Report schemas
class ReportBase(BaseModel):
    title: str
    content: str
    period_start: date
    period_end: date
    status: str = "draft"

class ReportCreate(ReportBase):
    cabinet_id: int

class ReportUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    status: Optional[str] = None

class ReportInDB(ReportBase):
    id: int
    cabinet_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Report(ReportInDB):
    pass

# Task schemas
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "new"
    priority: str = "medium"
    due_date: Optional[date] = None
    external_id: Optional[str] = None

class TaskCreate(TaskBase):
    cabinet_id: int
    report_id: Optional[int] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[date] = None
    external_id: Optional[str] = None
    report_id: Optional[int] = None

class TaskInDB(TaskBase):
    id: int
    cabinet_id: int
    report_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Task(TaskInDB):
    pass

# Analysis schemas
class AnalysisBase(BaseModel):
    analysis_type: str
    parameters: Optional[Dict[str, Any]] = None

class AnalysisCreate(AnalysisBase):
    cabinet_id: int

class AnalysisResultBase(BaseModel):
    analysis_type: str
    result_data: Dict[str, Any]

class AnalysisResultCreate(AnalysisResultBase):
    uploaded_file_id: int

class AnalysisResultInDB(AnalysisResultBase):
    id: int
    uploaded_file_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class AnalysisResult(AnalysisResultInDB):
    pass

# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: Optional[Dict[str, Any]] = None

class TokenData(BaseModel):
    username: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

# Excel file processing schemas
class ExcelFileUpload(BaseModel):
    cabinet_id: int
    file_type: str = Field(..., description="Type of Excel file: 'metrics' or 'report_table'")

class ExcelAnalysisRequest(BaseModel):
    file_id: int
    analysis_type: str = Field(..., description="Type of analysis to perform: 'trends', 'competitors', 'metrics'")
    marketplace: Optional[str] = None  # ← добавляем это
    parameters: Optional[Dict[str, Any]] = None

class ExcelAnalysisResponse(BaseModel):
    analysis_id: int
    file_id: int
    analysis_type: str
    status: str
    result: Optional[Dict[str, Any]] = None
