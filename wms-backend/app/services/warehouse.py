import uuid
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Location, Warehouse
from app.schemas.schemas import LocationCreate, WarehouseCreate, WarehouseUpdate


async def _next_available_warehouse_code(db: AsyncSession, user_id: UUID, short_code: str) -> str:
    base_code = short_code.strip().upper()
    candidate = base_code
    suffix = 2

    while await db.scalar(
        select(Warehouse.id).where(
            Warehouse.short_code == candidate,
        )
    ):
        candidate = f"{base_code[: max(1, 20 - len(str(suffix)) - 1)]}-{suffix}"
        suffix += 1

    return candidate


async def create_warehouse(db: AsyncSession, data: WarehouseCreate, user_id: UUID) -> Warehouse:
    warehouse_data = data.model_dump()

    for _ in range(5):
        resolved_short_code = await _next_available_warehouse_code(db, user_id, warehouse_data["short_code"])
        wh = Warehouse(id=uuid.uuid4(), created_by=user_id, **{**warehouse_data, "short_code": resolved_short_code})
        db.add(wh)
        try:
            await db.flush()
            return wh
        except IntegrityError as exc:
            await db.rollback()
            message = str(getattr(exc, "orig", exc))
            if "short_code" in message or "warehouse" in message:
                warehouse_data["short_code"] = resolved_short_code
                continue
            raise HTTPException(status_code=400, detail=message) from exc

    raise HTTPException(status_code=400, detail="Unable to create warehouse right now")


async def get_warehouse(db: AsyncSession, warehouse_id: UUID, user_id: UUID) -> Warehouse:
    wh = await db.scalar(select(Warehouse).where(Warehouse.id == warehouse_id, Warehouse.created_by == user_id))
    if not wh:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return wh


async def list_warehouses(db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 50) -> list[Warehouse]:
    result = await db.scalars(
        select(Warehouse).where(Warehouse.created_by == user_id).offset(skip).limit(limit)
    )
    return list(result.all())


async def update_warehouse(db: AsyncSession, warehouse_id: UUID, data: WarehouseUpdate, user_id: UUID) -> Warehouse:
    wh = await get_warehouse(db, warehouse_id, user_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(wh, field, value)
    await db.flush()
    return wh


async def create_location(db: AsyncSession, warehouse_id: UUID, data: LocationCreate, user_id: UUID) -> Location:
    await get_warehouse(db, warehouse_id, user_id)
    duplicate_code = await db.scalar(
        select(Location).where(Location.warehouse_id == warehouse_id, Location.short_code == data.short_code)
    )
    if duplicate_code:
        raise HTTPException(status_code=400, detail="Location short code already exists in this warehouse")
    if data.barcode:
        duplicate_barcode = await db.scalar(select(Location).where(Location.barcode == data.barcode))
        if duplicate_barcode:
            raise HTTPException(status_code=400, detail="Barcode already in use")
    loc = Location(id=uuid.uuid4(), warehouse_id=warehouse_id, **data.model_dump())
    db.add(loc)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        detail = "Barcode already in use" if data.barcode else "Location short code already exists in this warehouse"
        raise HTTPException(status_code=400, detail=detail) from exc
    return loc


async def list_locations(db: AsyncSession, warehouse_id: UUID, user_id: UUID) -> list[Location]:
    await get_warehouse(db, warehouse_id, user_id)
    result = await db.scalars(select(Location).where(Location.warehouse_id == warehouse_id))
    return list(result.all())
