from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.core.security import get_current_active_user
from app.models.models import Report, AnalysisResult
from app.schemas.schemas import Report as ReportSchema
from app.schemas.schemas import ReportCreate, ReportUpdate

router = APIRouter()

@router.post("/", response_model=ReportSchema)
async def create_report(
    report: ReportCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Создание нового отчета
    
    - **title**: Заголовок отчета
    - **content**: Содержание отчета
    - **period_start**: Начало периода
    - **period_end**: Конец периода
    - **cabinet_id**: ID кабинета, к которому относится отчет
    - **status**: Статус отчета (draft, published)
    """
    db_report = Report(
        title=report.title,
        content=report.content,
        period_start=report.period_start,
        period_end=report.period_end,
        cabinet_id=report.cabinet_id,
        status=report.status
    )
    
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    return db_report

@router.get("/", response_model=List[ReportSchema])
async def get_reports(
    cabinet_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Получение списка отчетов
    
    - **cabinet_id**: Фильтр по ID кабинета (опционально)
    - **status**: Фильтр по статусу отчета (опционально)
    - **skip**: Количество записей для пропуска (пагинация)
    - **limit**: Максимальное количество записей для возврата (пагинация)
    """
    query = db.query(Report)
    
    if cabinet_id:
        query = query.filter(Report.cabinet_id == cabinet_id)
    
    if status:
        query = query.filter(Report.status == status)
    
    reports = query.order_by(Report.created_at.desc()).offset(skip).limit(limit).all()
    
    return reports

@router.get("/{report_id}", response_model=ReportSchema)
async def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Получение информации об отчете по ID
    
    - **report_id**: ID отчета
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    return report

@router.put("/{report_id}", response_model=ReportSchema)
async def update_report(
    report_id: int,
    report_update: ReportUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Обновление информации об отчете
    
    - **report_id**: ID отчета
    - **title**: Новый заголовок отчета (опционально)
    - **content**: Новое содержание отчета (опционально)
    - **period_start**: Новое начало периода (опционально)
    - **period_end**: Новый конец периода (опционально)
    - **status**: Новый статус отчета (опционально)
    """
    db_report = db.query(Report).filter(Report.id == report_id).first()
    
    if not db_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # Обновляем только предоставленные поля
    update_data = report_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_report, key, value)
    
    db.commit()
    db.refresh(db_report)
    
    return db_report

@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Удаление отчета
    
    - **report_id**: ID отчета для удаления
    """
    db_report = db.query(Report).filter(Report.id == report_id).first()
    
    if not db_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    db.delete(db_report)
    db.commit()
    
    return None

@router.post("/generate-from-analysis/{analysis_id}", response_model=ReportSchema)
async def generate_report_from_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Генерация отчета на основе результатов анализа
    
    - **analysis_id**: ID анализа, на основе которого генерируется отчет
    """
    # Получаем результаты анализа
    analysis_result = db.query(AnalysisResult).filter(AnalysisResult.id == analysis_id).first()
    
    if not analysis_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis result not found"
        )
    
    # Проверяем, что это анализ типа "metrics"
    if analysis_result.analysis_type != "metrics":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only generate report from metrics analysis"
        )
    
    # Получаем информацию о файле
    file = db.query(UploadedFile).filter(UploadedFile.id == analysis_result.uploaded_file_id).first()
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Создаем отчет на основе результатов анализа
    result_data = analysis_result.result_data
    
    db_report = Report(
        title=result_data.get("report_title", "Аналитический отчет"),
        content=result_data.get("report_content", ""),
        period_start=result_data.get("period_start"),
        period_end=result_data.get("period_end"),
        cabinet_id=file.cabinet_id,
        status="draft"
    )
    
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    return db_report
