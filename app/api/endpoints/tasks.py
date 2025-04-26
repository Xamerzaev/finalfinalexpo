from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.core.security import get_current_active_user
from app.models.models import Task, Report
from app.schemas.schemas import Task as TaskSchema
from app.schemas.schemas import TaskCreate, TaskUpdate

router = APIRouter()

@router.post("/", response_model=TaskSchema)
async def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Создание новой задачи
    
    - **title**: Заголовок задачи
    - **description**: Описание задачи (опционально)
    - **status**: Статус задачи (new, in_progress, completed)
    - **priority**: Приоритет задачи (low, medium, high)
    - **due_date**: Срок выполнения (опционально)
    - **cabinet_id**: ID кабинета, к которому относится задача
    - **report_id**: ID отчета, к которому относится задача (опционально)
    """
    db_task = Task(
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date,
        cabinet_id=task.cabinet_id,
        report_id=task.report_id
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    return db_task

@router.get("/", response_model=List[TaskSchema])
async def get_tasks(
    cabinet_id: Optional[int] = None,
    report_id: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Получение списка задач
    
    - **cabinet_id**: Фильтр по ID кабинета (опционально)
    - **report_id**: Фильтр по ID отчета (опционально)
    - **status**: Фильтр по статусу задачи (опционально)
    - **priority**: Фильтр по приоритету задачи (опционально)
    - **skip**: Количество записей для пропуска (пагинация)
    - **limit**: Максимальное количество записей для возврата (пагинация)
    """
    query = db.query(Task)
    
    if cabinet_id:
        query = query.filter(Task.cabinet_id == cabinet_id)
    
    if report_id:
        query = query.filter(Task.report_id == report_id)
    
    if status:
        query = query.filter(Task.status == status)
    
    if priority:
        query = query.filter(Task.priority == priority)
    
    tasks = query.order_by(Task.created_at.desc()).offset(skip).limit(limit).all()
    
    return tasks

@router.get("/{task_id}", response_model=TaskSchema)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Получение информации о задаче по ID
    
    - **task_id**: ID задачи
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return task

@router.put("/{task_id}", response_model=TaskSchema)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Обновление информации о задаче
    
    - **task_id**: ID задачи
    - **title**: Новый заголовок задачи (опционально)
    - **description**: Новое описание задачи (опционально)
    - **status**: Новый статус задачи (опционально)
    - **priority**: Новый приоритет задачи (опционально)
    - **due_date**: Новый срок выполнения (опционально)
    - **report_id**: Новый ID отчета (опционально)
    """
    db_task = db.query(Task).filter(Task.id == task_id).first()
    
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Обновляем только предоставленные поля
    update_data = task_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_task, key, value)
    
    db.commit()
    db.refresh(db_task)
    
    return db_task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Удаление задачи
    
    - **task_id**: ID задачи для удаления
    """
    db_task = db.query(Task).filter(Task.id == task_id).first()
    
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    db.delete(db_task)
    db.commit()
    
    return None

@router.post("/generate-from-report/{report_id}", response_model=List[TaskSchema])
async def generate_tasks_from_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Генерация задач на основе отчета
    
    - **report_id**: ID отчета, на основе которого генерируются задачи
    """
    # Получаем отчет
    report = db.query(Report).filter(Report.id == report_id).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # Анализируем содержимое отчета для выделения рекомендаций
    # Это можно сделать с помощью OpenAI API или другого метода анализа текста
    # Для простоты сейчас создадим одну задачу с общим описанием
    
    db_task = Task(
        title=f"Задача на основе отчета: {report.title}",
        description=f"Выполнить рекомендации из отчета от {report.period_start} до {report.period_end}",
        status="new",
        priority="medium",
        cabinet_id=report.cabinet_id,
        report_id=report.id
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    return [db_task]
