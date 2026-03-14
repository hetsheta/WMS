from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user
from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import LocationSummary, ProductSummary, StockAdjust, StockItemOut
from app.services import stock as stock_svc

router = APIRouter(prefix="/stock", tags=["stock"])


@router.get("", response_model=list[StockItemOut])
async def list_stock(
    warehouse_id: UUID | None = Query(default=None),
    product_id: UUID | None = Query(default=None),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    items = await stock_svc.list_stock(db, user.id, warehouse_id, product_id, skip, limit)
    return [
        StockItemOut(
            id=item.id,
            product_id=item.product_id,
            location_id=item.location_id,
            on_hand=item.on_hand,
            reserved=item.reserved,
            free_to_use=item.free_to_use,
            updated_at=item.updated_at,
            product=ProductSummary.model_validate(item.product) if item.product else None,
            location=LocationSummary.model_validate(item.location) if item.location else None,
        )
        for item in items
    ]


@router.post("/adjust", response_model=StockItemOut)
async def adjust(data: StockAdjust, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    item = await stock_svc.manual_adjustment(db, data.product_id, data.location_id, data.quantity, user.id)
    return StockItemOut(
        id=item.id,
        product_id=item.product_id,
        location_id=item.location_id,
        on_hand=item.on_hand,
        reserved=item.reserved,
        free_to_use=item.free_to_use,
        updated_at=item.updated_at,
        product=ProductSummary.model_validate(item.product) if item.product else None,
        location=LocationSummary.model_validate(item.location) if item.location else None,
    )
