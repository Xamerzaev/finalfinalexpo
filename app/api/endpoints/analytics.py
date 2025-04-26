from typing import Dict, List, Any, Optional
import logging
import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Path
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.excel_data_processor import ExcelDataProcessor
from app.services.openai_service import openai_service
from app.models.models import AnalysisResult
from app.schemas.schemas import ExcelAnalysisRequest

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Хранилище результатов анализа в памяти (для демонстрации)
analysis_results: Dict[int, Dict[str, Any]] = {}


@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_file(
    request: ExcelAnalysisRequest,
    db: Session = Depends(get_db)
):
    file_id = request.file_id
    analysis_type = request.analysis_type
    marketplace = request.marketplace
    parameters = request.parameters or {}
    """
    Анализирует загруженный файл и возвращает результаты анализа
    
    Args:
        file_id: ID файла для анализа
        marketplace: Название маркетплейса (опционально)
        analysis_type: Тип анализа (опционально)
        db: Сессия базы данных
        
    Returns:
        Результаты анализа или статус задачи
    """
    try:
        logger.info(f"Starting analysis for file_id: {file_id}, marketplace: {marketplace}, analysis_type: {analysis_type}")
        
        # Создаем процессор для работы с Excel
        excel_processor = ExcelDataProcessor()
        logger.info(f"Processing file with ID: {file_id}")
        file_data = excel_processor.process_file_by_id(file_id, db=db)
        print(file_data)
        if not file_data:
            logger.error(f"File with ID {file_id} not found or could not be processed")
            raise HTTPException(status_code=404, detail="File not found or could not be processed")
        
        logger.info(f"File processed successfully, data keys: {list(file_data.keys()) if isinstance(file_data, dict) else 'not a dict'}")
        
        # Запускаем анализ данных напрямую (без фоновых задач)
        try:
            logger.info("Calling OpenAI service for analysis")
            analysis_result = await openai_service.analyze_raw_data(file_data, marketplace, analysis_type)
            logger.info(f"Analysis completed, result type: {type(analysis_result)}")
            
            # Проверяем, что результат - словарь
            if not isinstance(analysis_result, dict):
                logger.warning(f"Analysis result is not a dictionary: {type(analysis_result)}")
                analysis_result = {"trends_analysis": str(analysis_result)}
            
            # Сохраняем результат в хранилище
            analysis_results[file_id] = analysis_result
            logger.info(f"Analysis result saved for file_id: {file_id}")
            
            # Возвращаем результат
            return {
                "status": "completed",
                "file_id": file_id,
                "result": analysis_result
            }
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}")
            return {
                "status": "error",
                "file_id": file_id,
                "error": str(e)
            }
    except Exception as e:
        logger.error(f"Error in analyze_file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/result/{file_id}", response_model=Dict[str, Any])
async def get_analysis_result(
    file_id: int = Path(..., description="ID файла, для которого нужно получить результаты анализа")
):
    """
    Возвращает результаты анализа для указанного файла
    
    Args:
        file_id: ID файла
        
    Returns:
        Результаты анализа
    """
    try:
        # Проверяем, есть ли результат в хранилище
        if file_id not in analysis_results:
            raise HTTPException(status_code=404, detail="Analysis result not found")
        
        # Возвращаем результат
        return {
            "status": "completed",
            "file_id": file_id,
            "result": analysis_results[file_id]
        }
    except Exception as e:
        logger.error(f"Error in get_analysis_result: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/file/{file_id}", response_model=Dict[str, Any])
async def get_analysis_by_file(
    file_id: int = Path(..., description="ID файла для которого нужно получить результаты анализа"),
    analysis_type: Optional[str] = Query(None, description="Тип анализа (опционально)")
):
    if file_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    # Возвращаем полный результат, игнорируя analysis_type
    return {
        "status": "completed",
        "file_id": file_id,
        "result": analysis_results[file_id]
    }
