from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import pandas as pd
import os
import logging

from app.db.session import get_db
from app.services.excel_data_processor import excel_processor
from app.services.openai_service import openai_service
from app.services.metrics_analyzer import metrics_analyzer
from app.services.task_manager import task_manager
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload-excel/")
async def upload_excel_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Загружает Excel-файл для анализа
    """
    try:
        # Создаем директорию для загрузок, если она не существует
        os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
        
        # Сохраняем файл
        file_path = os.path.join(settings.UPLOAD_FOLDER, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        # Обрабатываем файл в фоновом режиме
        background_tasks.add_task(excel_processor.process_file, file_path)
        
        return {"message": "Файл успешно загружен и поставлен в очередь на обработку", "filename": file.filename}
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при загрузке файла: {str(e)}")

@router.get("/analysis/categories/")
async def analyze_by_categories(
    data_id: Optional[int] = None,
    category_column: Optional[str] = "category",
    db: Session = Depends(get_db)
):
    """
    Анализирует данные по категориям
    """
    try:
        # Получаем данные для анализа
        data = excel_processor.get_processed_data(data_id)
        if not data:
            raise HTTPException(status_code=404, detail="Данные не найдены")
        
        # Анализируем данные по категориям
        result = metrics_analyzer.analyze_by_category(data, category_column)
        
        # Проверяем наличие ошибок
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing by categories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при анализе по категориям: {str(e)}")

@router.get("/analysis/products/")
async def analyze_by_products(
    data_id: Optional[int] = None,
    product_column: Optional[str] = "product_id",
    db: Session = Depends(get_db)
):
    """
    Анализирует данные по товарам
    """
    try:
        # Получаем данные для анализа
        data = excel_processor.get_processed_data(data_id)
        if not data:
            raise HTTPException(status_code=404, detail="Данные не найдены")
        
        # Анализируем данные по товарам
        result = metrics_analyzer.analyze_by_product(data, product_column)
        
        # Проверяем наличие ошибок
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing by products: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при анализе по товарам: {str(e)}")

@router.get("/analysis/accounts/")
async def analyze_by_accounts(
    data_id: Optional[int] = None,
    account_column: Optional[str] = "account_id",
    db: Session = Depends(get_db)
):
    """
    Анализирует данные по кабинетам
    """
    try:
        # Получаем данные для анализа
        data = excel_processor.get_processed_data(data_id)
        if not data:
            raise HTTPException(status_code=404, detail="Данные не найдены")
        
        # Анализируем данные по кабинетам
        result = metrics_analyzer.analyze_by_account(data, account_column)
        
        # Проверяем наличие ошибок
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing by accounts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при анализе по кабинетам: {str(e)}")

@router.get("/analysis/ad-sources/")
async def analyze_ad_sources(
    data_id: Optional[int] = None,
    source_column: Optional[str] = "source",
    db: Session = Depends(get_db)
):
    """
    Анализирует данные по рекламным источникам
    """
    try:
        # Получаем данные для анализа
        data = excel_processor.get_processed_data(data_id)
        if not data:
            raise HTTPException(status_code=404, detail="Данные не найдены")
        
        # Анализируем данные по рекламным источникам
        result = metrics_analyzer.analyze_ad_sources(data, source_column)
        
        # Проверяем наличие ошибок
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing ad sources: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при анализе рекламных источников: {str(e)}")

@router.get("/analysis/orders-decline/")
async def analyze_orders_decline(
    data_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Анализирует причины падения заказов
    """
    try:
        # Получаем данные для анализа
        data = excel_processor.get_processed_data(data_id)
        if not data:
            raise HTTPException(status_code=404, detail="Данные не найдены")
        
        # Анализируем причины падения заказов
        result = metrics_analyzer.analyze_orders_decline(data)
        
        # Проверяем наличие ошибок
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing orders decline: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при анализе причин падения заказов: {str(e)}")

@router.get("/analysis/ad-effectiveness/")
async def analyze_ad_effectiveness(
    data_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Анализирует эффективность рекламных инструментов
    """
    try:
        # Получаем данные для анализа
        data = excel_processor.get_processed_data(data_id)
        if not data:
            raise HTTPException(status_code=404, detail="Данные не найдены")
        
        # Анализируем эффективность рекламных инструментов
        result = metrics_analyzer.analyze_ad_effectiveness(data)
        
        # Проверяем наличие ошибок
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing ad effectiveness: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при анализе эффективности рекламных инструментов: {str(e)}")

@router.get("/analysis/seasonality/")
async def analyze_seasonality(
    data_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Анализирует сезонность в данных
    """
    try:
        # Получаем данные для анализа
        data = excel_processor.get_processed_data(data_id)
        if not data:
            raise HTTPException(status_code=404, detail="Данные не найдены")
        
        # Анализируем сезонность
        result = metrics_analyzer.analyze_seasonality(data)
        
        # Проверяем наличие ошибок
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing seasonality: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при анализе сезонности: {str(e)}")

@router.post("/tasks/create/")
async def create_task(
    title: str = Form(...),
    description: str = Form(...),
    category: Optional[str] = Form("analytics"),
    priority: Optional[str] = Form("medium"),
    due_date: Optional[str] = Form(None),
    assignee: Optional[str] = Form(None),
    related_metrics: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Создает новую задачу
    """
    try:
        # Преобразуем связанные метрики из строки JSON в список
        metrics_list = []
        if related_metrics:
            try:
                metrics_list = json.loads(related_metrics)
            except:
                metrics_list = []
        
        # Создаем задачу
        task = task_manager.create_task(
            title=title,
            description=description,
            category=category,
            priority=priority,
            due_date=due_date,
            assignee=assignee,
            related_metrics=metrics_list
        )
        
        return task
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при создании задачи: {str(e)}")

@router.get("/tasks/")
async def get_tasks(
    category: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Получает список задач с фильтрацией
    """
    try:
        # Получаем задачи с фильтрацией
        tasks = task_manager.get_tasks(
            category=category,
            priority=priority,
            status=status
        )
        
        return {"tasks": tasks}
    except Exception as e:
        logger.error(f"Error getting tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при получении задач: {str(e)}")

@router.put("/tasks/{task_id}/")
async def update_task(
    task_id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    priority: Optional[str] = Form(None),
    due_date: Optional[str] = Form(None),
    assignee: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    related_metrics: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Обновляет задачу
    """
    try:
        # Формируем обновления
        updates = {}
        if title is not None:
            updates["title"] = title
        if description is not None:
            updates["description"] = description
        if category is not None:
            updates["category"] = category
        if priority is not None:
            updates["priority"] = priority
        if due_date is not None:
            updates["due_date"] = due_date
        if assignee is not None:
            updates["assignee"] = assignee
        if status is not None:
            updates["status"] = status
        if related_metrics is not None:
            try:
                updates["related_metrics"] = json.loads(related_metrics)
            except:
                updates["related_metrics"] = []
        
        # Обновляем задачу
        task = task_manager.update_task(task_id, updates)
        
        # Проверяем, найдена ли задача
        if task is None:
            raise HTTPException(status_code=404, detail=f"Задача с ID {task_id} не найдена")
        
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении задачи: {str(e)}")

@router.delete("/tasks/{task_id}/")
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    Удаляет задачу
    """
    try:
        # Удаляем задачу
        success = task_manager.delete_task(task_id)
        
        # Проверяем, найдена ли задача
        if not success:
            raise HTTPException(status_code=404, detail=f"Задача с ID {task_id} не найдена")
        
        return {"message": f"Задача с ID {task_id} успешно удалена"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении задачи: {str(e)}")

@router.post("/tasks/generate-from-analysis/")
async def generate_tasks_from_analysis(
    analysis_result: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Генерирует задачи на основе результатов анализа
    """
    try:
        # Генерируем задачи
        tasks = task_manager.generate_tasks_from_analysis(analysis_result)
        
        return {"tasks": tasks}
    except Exception as e:
        logger.error(f"Error generating tasks from analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации задач из анализа: {str(e)}")

@router.post("/tasks/generate-from-metrics/")
async def generate_tasks_from_metrics(
    metrics_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Генерирует задачи на основе метрик
    """
    try:
        # Генерируем задачи
        tasks = task_manager.generate_tasks_from_metrics(metrics_data)
        
        return {"tasks": tasks}
    except Exception as e:
        logger.error(f"Error generating tasks from metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации задач из метрик: {str(e)}")

@router.get("/tasks/prioritize/")
async def prioritize_tasks(
    db: Session = Depends(get_db)
):
    """
    Приоритизирует задачи
    """
    try:
        # Приоритизируем задачи
        tasks = task_manager.prioritize_tasks()
        
        return {"tasks": tasks}
    except Exception as e:
        logger.error(f"Error prioritizing tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при приоритизации задач: {str(e)}")
