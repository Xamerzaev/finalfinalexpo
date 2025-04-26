from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.core.security import get_current_active_user
from app.models.models import Cabinet
from app.schemas.schemas import Cabinet as CabinetSchema
from app.schemas.schemas import CabinetCreate, CabinetUpdate

router = APIRouter()

@router.post("/", response_model=CabinetSchema)
async def create_cabinet(
    cabinet: CabinetCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Создание нового кабинета маркетплейса
    
    - **name**: Название кабинета
    - **marketplace**: Маркетплейс (ozon или wildberries)
    - **project_id**: ID проекта, к которому относится кабинет
    - **api_key**: API ключ (опционально)
    - **api_secret**: API секрет (опционально)
    """
    db_cabinet = Cabinet(
        name=cabinet.name,
        marketplace=cabinet.marketplace,
        project_id=cabinet.project_id,
        api_key=cabinet.api_key,
        api_secret=cabinet.api_secret
    )
    
    db.add(db_cabinet)
    db.commit()
    db.refresh(db_cabinet)
    
    return db_cabinet

@router.get("/", response_model=List[CabinetSchema])
async def get_cabinets(
    project_id: Optional[int] = None,
    marketplace: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Получение списка кабинетов
    
    - **project_id**: Фильтр по ID проекта (опционально)
    - **marketplace**: Фильтр по маркетплейсу (опционально)
    - **skip**: Количество записей для пропуска (пагинация)
    - **limit**: Максимальное количество записей для возврата (пагинация)
    """
    query = db.query(Cabinet)
    
    if project_id:
        query = query.filter(Cabinet.project_id == project_id)
    
    if marketplace:
        query = query.filter(Cabinet.marketplace == marketplace)
    
    cabinets = query.offset(skip).limit(limit).all()
    
    return cabinets

@router.get("/{cabinet_id}", response_model=CabinetSchema)
async def get_cabinet(
    cabinet_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Получение информации о кабинете по ID
    
    - **cabinet_id**: ID кабинета
    """
    cabinet = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
    
    if not cabinet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cabinet not found"
        )
    
    return cabinet

@router.put("/{cabinet_id}", response_model=CabinetSchema)
async def update_cabinet(
    cabinet_id: int,
    cabinet_update: CabinetUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Обновление информации о кабинете
    
    - **cabinet_id**: ID кабинета
    - **name**: Новое название кабинета (опционально)
    - **marketplace**: Новый маркетплейс (опционально)
    - **api_key**: Новый API ключ (опционально)
    - **api_secret**: Новый API секрет (опционально)
    """
    db_cabinet = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
    
    if not db_cabinet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cabinet not found"
        )
    
    # Обновляем только предоставленные поля
    update_data = cabinet_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_cabinet, key, value)
    
    db.commit()
    db.refresh(db_cabinet)
    
    return db_cabinet

@router.delete("/{cabinet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cabinet(
    cabinet_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Удаление кабинета
    
    - **cabinet_id**: ID кабинета для удаления
    """
    db_cabinet = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
    
    if not db_cabinet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cabinet not found"
        )
    
    db.delete(db_cabinet)
    db.commit()
    
    return None
