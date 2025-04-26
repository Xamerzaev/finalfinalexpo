from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime

from app.db.session import get_db
from app.core.security import get_current_active_user
from app.models.models import UploadedFile, Cabinet
from app.schemas.schemas import UploadedFile as UploadedFileSchema
from app.schemas.schemas import UploadedFileCreate
from app.core.config import settings
from app.services.excel_data_processor import excel_data_processor

router = APIRouter()

@router.post("/upload", response_model=UploadedFileSchema)
async def upload_file(
    file: UploadFile = File(...),
    cabinet_id: int = Form(...),
    file_type: str = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Загрузка Excel-файла с данными маркетплейса
    
    - **file**: Excel-файл для загрузки
    - **cabinet_id**: ID кабинета, к которому относится файл
    - **file_type**: Тип файла (metrics или report_table)
    """
    # Проверяем существование кабинета
    cabinet = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
    if not cabinet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cabinet not found"
        )
    
    # Проверяем тип файла
    if file_type not in ["metrics", "report_table"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Must be 'metrics' or 'report_table'"
        )
    
    # Проверяем расширение файла
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in [".xlsx", ".xls", ".csv"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Must be Excel (.xlsx, .xls) or CSV (.csv)"
        )
    
    # Создаем директорию для загрузки, если она не существует
    upload_dir = os.path.join(settings.UPLOAD_FOLDER, str(cabinet_id))
    os.makedirs(upload_dir, exist_ok=True)
    
    # Генерируем уникальное имя файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{file_type}_{timestamp}{file_extension}"
    file_path = os.path.join(upload_dir, file_name)
    
    # Сохраняем файл
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Создаем запись в базе данных
    db_file = UploadedFile(
        cabinet_id=cabinet_id,
        original_filename=file.filename,
        file_path=file_path,
        file_type=file_type,
        processed=False
    )
    
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    # Запускаем обработку файла в фоновом режиме
    # Это можно реализовать через Celery или другой механизм фоновых задач
    # Для простоты сейчас просто отмечаем, что файл обработан
    try:
        # Обрабатываем файл
        excel_data_processor.process_file(db_file.id, db)
        
        # Обновляем статус обработки
        db_file.processed = True
        db.commit()
    except Exception as e:
        # В случае ошибки логируем её, но не прерываем выполнение
        print(f"Error processing file: {str(e)}")
    
    return db_file

@router.get("/files", response_model=List[UploadedFileSchema])
async def get_files(
    cabinet_id: Optional[int] = None,
    file_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Получение списка загруженных файлов
    
    - **cabinet_id**: Фильтр по ID кабинета (опционально)
    - **file_type**: Фильтр по типу файла (опционально)
    - **skip**: Количество записей для пропуска (пагинация)
    - **limit**: Максимальное количество записей для возврата (пагинация)
    """
    query = db.query(UploadedFile)
    
    if cabinet_id:
        query = query.filter(UploadedFile.cabinet_id == cabinet_id)
    
    if file_type:
        query = query.filter(UploadedFile.file_type == file_type)
    
    files = query.order_by(UploadedFile.upload_date.desc()).offset(skip).limit(limit).all()
    
    return files

@router.get("/files/{file_id}", response_model=UploadedFileSchema)
async def get_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Получение информации о загруженном файле по ID
    
    - **file_id**: ID файла
    """
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return file

@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Удаление загруженного файла
    
    - **file_id**: ID файла для удаления
    """
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Удаляем физический файл
    try:
        if os.path.exists(file.file_path):
            os.remove(file.file_path)
    except Exception as e:
        # Логируем ошибку, но продолжаем удаление записи из БД
        print(f"Error deleting file {file.file_path}: {str(e)}")
    
    # Удаляем запись из БД
    db.delete(file)
    db.commit()
    
    return None
