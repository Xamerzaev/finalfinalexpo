from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, date

from app.db.session import get_db
from app.core.security import get_current_active_user
from app.models.models import AnalysisResult, UploadedFile, Cabinet
from app.schemas.schemas import AnalysisResult as AnalysisResultSchema
from app.schemas.schemas import ExcelAnalysisRequest, ExcelAnalysisResponse
from app.services.openai_service import openai_service
from app.services.excel_data_processor import excel_data_processor

router = APIRouter()

@router.post("/analyze", response_model=ExcelAnalysisResponse)
async def analyze_excel_data(
    request: ExcelAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Анализ данных из Excel-файла с использованием ИИ
    
    - **file_id**: ID загруженного файла
    - **analysis_type**: Тип анализа (trends, competitors, metrics)
    - **parameters**: Дополнительные параметры для анализа
    """
    # Проверяем существование файла
    file = db.query(UploadedFile).filter(UploadedFile.id == request.file_id).first()
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Проверяем, что файл обработан
    if not file.processed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is not processed yet"
        )
    
    # Получаем кабинет
    cabinet = db.query(Cabinet).filter(Cabinet.id == file.cabinet_id).first()
    if not cabinet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cabinet not found"
        )
    
    # Получаем результаты обработки файла
    file_processing_result = db.query(AnalysisResult).filter(
        AnalysisResult.uploaded_file_id == file.id,
        AnalysisResult.analysis_type == "file_processing"
    ).first()
    
    if not file_processing_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File processing results not found"
        )
    
    # Выполняем анализ в зависимости от типа
    analysis_result = None
    
    if request.analysis_type == "trends":
        # Анализ трендов
        period = request.parameters.get("period", "month") if request.parameters else "month"
        
        # Извлекаем метрики из результатов обработки файла
        metrics_data = {}
        if file.file_type == "metrics" and file_processing_result.result_data.get("metrics_data"):
            for metric in file_processing_result.result_data.get("metrics_data", []):
                metric_name = metric.get("metric_name")
                if metric_name not in metrics_data:
                    metrics_data[metric_name] = []
                metrics_data[metric_name].append(metric.get("value"))
        else:
            # Если файл не содержит метрик, используем статистику из отчетной таблицы
            numeric_stats = file_processing_result.result_data.get("numeric_stats", {})
            for col_name, stats in numeric_stats.items():
                metrics_data[col_name] = stats
        
        # Выполняем анализ трендов
        trends_analysis = openai_service.analyze_trends(metrics_data, period)
        
        # Сохраняем результаты анализа
        analysis_result = AnalysisResult(
            uploaded_file_id=file.id,
            analysis_type=request.analysis_type,
            result_data=trends_analysis
        )
        
    elif request.analysis_type == "competitors":
        # Анализ конкурентов
        marketplace = cabinet.marketplace
        category = request.parameters.get("category", "") if request.parameters else ""
        competitors = request.parameters.get("competitors", []) if request.parameters else []
        
        # Извлекаем наши метрики из результатов обработки файла
        our_metrics = {}
        if file.file_type == "metrics" and file_processing_result.result_data.get("metrics_data"):
            for metric in file_processing_result.result_data.get("metrics_data", []):
                metric_name = metric.get("metric_name")
                if metric_name not in our_metrics:
                    our_metrics[metric_name] = []
                our_metrics[metric_name].append(metric.get("value"))
            
            # Преобразуем списки значений в средние значения
            for metric_name, values in our_metrics.items():
                if values:
                    our_metrics[metric_name] = sum(values) / len(values)
        else:
            # Если файл не содержит метрик, используем статистику из отчетной таблицы
            numeric_stats = file_processing_result.result_data.get("numeric_stats", {})
            for col_name, stats in numeric_stats.items():
                our_metrics[col_name] = stats.get("mean")
        
        # Выполняем анализ конкурентов
        competitors_analysis = openai_service.analyze_competitors(
            marketplace, category, competitors, our_metrics
        )
        
        # Сохраняем результаты анализа
        analysis_result = AnalysisResult(
            uploaded_file_id=file.id,
            analysis_type=request.analysis_type,
            result_data=competitors_analysis
        )
        
    elif request.analysis_type == "metrics":
        # Анализ метрик и генерация отчета
        marketplace = cabinet.marketplace
        period_start = request.parameters.get("period_start", "") if request.parameters else ""
        period_end = request.parameters.get("period_end", "") if request.parameters else ""
        
        if not period_start or not period_end:
            # Если период не указан, используем данные из файла
            date_stats = file_processing_result.result_data.get("date_stats", {})
            for col_name, stats in date_stats.items():
                if "min_date" in stats and "max_date" in stats:
                    period_start = stats["min_date"]
                    period_end = stats["max_date"]
                    break
            
            # Если период все еще не определен, используем текущую дату
            if not period_start or not period_end:
                today = datetime.now().date().isoformat()
                period_start = period_end = today
        
        # Извлекаем метрики из результатов обработки файла
        metrics_data = {}
        if file.file_type == "metrics" and file_processing_result.result_data.get("metrics_data"):
            for metric in file_processing_result.result_data.get("metrics_data", []):
                metric_name = metric.get("metric_name")
                if metric_name not in metrics_data:
                    metrics_data[metric_name] = []
                metrics_data[metric_name].append(metric.get("value"))
            
            # Преобразуем списки значений в средние значения
            for metric_name, values in metrics_data.items():
                if values:
                    metrics_data[metric_name] = sum(values) / len(values)
        else:
            # Если файл не содержит метрик, используем статистику из отчетной таблицы
            numeric_stats = file_processing_result.result_data.get("numeric_stats", {})
            for col_name, stats in numeric_stats.items():
                metrics_data[col_name] = stats.get("mean")
        
        # Получаем результаты предыдущих анализов (если есть)
        trends_analysis = db.query(AnalysisResult).filter(
            AnalysisResult.uploaded_file_id == file.id,
            AnalysisResult.analysis_type == "trends"
        ).first()
        
        competitors_analysis = db.query(AnalysisResult).filter(
            AnalysisResult.uploaded_file_id == file.id,
            AnalysisResult.analysis_type == "competitors"
        ).first()
        
        # Генерируем отчет
        report = openai_service.generate_report(
            marketplace,
            metrics_data,
            period_start,
            period_end,
            trends_analysis.result_data if trends_analysis else None,
            competitors_analysis.result_data if competitors_analysis else None
        )
        
        # Сохраняем результаты анализа
        analysis_result = AnalysisResult(
            uploaded_file_id=file.id,
            analysis_type=request.analysis_type,
            result_data=report
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported analysis type: {request.analysis_type}"
        )
    
    # Сохраняем результаты анализа в БД
    db.add(analysis_result)
    db.commit()
    db.refresh(analysis_result)
    
    return {
        "analysis_id": analysis_result.id,
        "file_id": file.id,
        "analysis_type": request.analysis_type,
        "status": "completed",
        "result": analysis_result.result_data
    }

@router.get("/results/{analysis_id}", response_model=AnalysisResultSchema)
async def get_analysis_result(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Получение результатов анализа по ID
    
    - **analysis_id**: ID анализа
    """
    analysis_result = db.query(AnalysisResult).filter(AnalysisResult.id == analysis_id).first()
    
    if not analysis_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis result not found"
        )
    
    return analysis_result

@router.get("/results/file/{file_id}", response_model=List[AnalysisResultSchema])
async def get_file_analysis_results(
    file_id: int,
    analysis_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Получение всех результатов анализа для файла
    
    - **file_id**: ID файла
    - **analysis_type**: Фильтр по типу анализа (опционально)
    """
    query = db.query(AnalysisResult).filter(AnalysisResult.uploaded_file_id == file_id)
    
    if analysis_type:
        query = query.filter(AnalysisResult.analysis_type == analysis_type)
    
    analysis_results = query.all()
    
    return analysis_results
