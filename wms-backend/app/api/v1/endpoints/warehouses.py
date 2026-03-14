from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.deps import current_user
from app.models.models import User
from app.schemas.schemas import WarehouseCreate, WarehouseUpdate, WarehouseOut, LocationCreate, LocationOut
from app.services import warehouse as wh_svc

router = APIRouter(prefix="/warehouses", tags=["warehouses"])


@router.post("", response_model=WarehouseOut, status_code=201)
async def create(data: WarehouseCreate, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return await wh_svc.create_warehouse(db, data, user.id)


@router.get("", response_model=list[WarehouseOut])
async def list_all(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return await wh_svc.list_warehouses(db, user.id, skip, limit)


@router.get("/{warehouse_id}", response_model=WarehouseOut)
async def get(warehouse_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return await wh_svc.get_warehouse(db, warehouse_id, user.id)


@router.patch("/{warehouse_id}", response_model=WarehouseOut)
async def update(warehouse_id: UUID, data: WarehouseUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return await wh_svc.update_warehouse(db, warehouse_id, data, user.id)


@router.post("/{warehouse_id}/locations", response_model=LocationOut, status_code=201)
async def create_location(warehouse_id: UUID, data: LocationCreate, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return await wh_svc.create_location(db, warehouse_id, data, user.id)


@router.get("/{warehouse_id}/locations", response_model=list[LocationOut])
async def list_locations(warehouse_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return await wh_svc.list_locations(db, warehouse_id, user.id)
