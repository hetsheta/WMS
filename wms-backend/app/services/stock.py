import uuid
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import Location, Product, StockItem, Warehouse


async def get_stock_item(db: AsyncSession, product_id: UUID, location_id: UUID, for_update: bool = False) -> StockItem | None:
    query = (
        select(StockItem)
        .options(selectinload(StockItem.product), selectinload(StockItem.location))
        .where(StockItem.product_id == product_id, StockItem.location_id == location_id)
    )
    if for_update:
        query = query.with_for_update()
    return await db.scalar(query)


async def get_or_create_stock_item(db: AsyncSession, product_id: UUID, location_id: UUID) -> StockItem:
    item = await get_stock_item(db, product_id, location_id, for_update=True)
    if not item:
        item = StockItem(
            id=uuid.uuid4(),
            product_id=product_id,
            location_id=location_id,
            on_hand=Decimal("0"),
            reserved=Decimal("0"),
        )
        db.add(item)
        await db.flush()
    return item


async def adjust_stock(
    db: AsyncSession,
    product_id: UUID,
    location_id: UUID,
    delta: Decimal,
    reserve_delta: Decimal = Decimal("0"),
) -> StockItem:
    item = await get_or_create_stock_item(db, product_id, location_id)
    new_on_hand = item.on_hand + delta
    new_reserved = item.reserved + reserve_delta
    new_free = new_on_hand - new_reserved

    if new_on_hand < 0:
        raise HTTPException(status_code=400, detail="Insufficient stock: on-hand would go negative")
    if new_free < 0:
        raise HTTPException(status_code=400, detail="Insufficient free-to-use stock")

    item.on_hand = new_on_hand
    item.reserved = new_reserved
    await db.flush()
    return item


async def list_stock(
    db: AsyncSession,
    user_id: UUID,
    warehouse_id: UUID | None = None,
    product_id: UUID | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[StockItem]:
    query = (
        select(StockItem)
        .options(selectinload(StockItem.product), selectinload(StockItem.location))
        .join(Product, StockItem.product_id == Product.id)
        .join(Location, StockItem.location_id == Location.id)
        .join(Warehouse, Location.warehouse_id == Warehouse.id)
        .where(Product.created_by == user_id, Warehouse.created_by == user_id)
    )
    if product_id:
        query = query.where(StockItem.product_id == product_id)
    if warehouse_id:
        query = query.where(Location.warehouse_id == warehouse_id)
    result = await db.scalars(query.offset(skip).limit(limit))
    return list(result.all())


async def manual_adjustment(
    db: AsyncSession,
    product_id: UUID,
    location_id: UUID,
    quantity: Decimal,
    user_id: UUID,
) -> StockItem:
    await _validate_product_location(db, product_id, location_id, user_id)
    await adjust_stock(db, product_id, location_id, delta=quantity)
    return await get_stock_item(db, product_id, location_id)


async def _validate_product_location(db: AsyncSession, product_id: UUID, location_id: UUID, user_id: UUID):
    product = await db.scalar(select(Product).where(Product.id == product_id, Product.created_by == user_id))
    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found")
    location = await db.scalar(
        select(Location)
        .join(Warehouse, Location.warehouse_id == Warehouse.id)
        .where(Location.id == location_id, Warehouse.created_by == user_id)
    )
    if not location or not location.is_active:
        raise HTTPException(status_code=404, detail="Location not found")
