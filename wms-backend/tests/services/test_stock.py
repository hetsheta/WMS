import pytest
from decimal import Decimal
import uuid
from app.services.stock import adjust_stock, get_or_create_stock_item
from app.models.models import Warehouse, Location, Product


@pytest.mark.asyncio
async def test_stock_created_on_first_adjust(db):
    wh = Warehouse(id=uuid.uuid4(), name="Test WH", short_code="TWH")
    loc = Location(id=uuid.uuid4(), warehouse_id=wh.id, name="Loc1", short_code="L1")
    prod = Product(id=uuid.uuid4(), name="Item", sku="ITM-001")
    db.add_all([wh, loc, prod])
    await db.flush()

    item = await adjust_stock(db, prod.id, loc.id, delta=Decimal("20"))
    assert item.on_hand == Decimal("20")
    assert item.reserved == Decimal("0")
    assert item.free_to_use == Decimal("20")


@pytest.mark.asyncio
async def test_stock_decrements(db):
    wh = Warehouse(id=uuid.uuid4(), name="WH4", short_code="WH4")
    loc = Location(id=uuid.uuid4(), warehouse_id=wh.id, name="Loc2", short_code="L2")
    prod = Product(id=uuid.uuid4(), name="Item2", sku="ITM-002")
    db.add_all([wh, loc, prod])
    await db.flush()

    await adjust_stock(db, prod.id, loc.id, delta=Decimal("10"))
    item = await adjust_stock(db, prod.id, loc.id, delta=Decimal("-3"))
    assert item.on_hand == Decimal("7")


@pytest.mark.asyncio
async def test_stock_cannot_go_negative(db):
    from fastapi import HTTPException
    wh = Warehouse(id=uuid.uuid4(), name="WH5", short_code="WH5")
    loc = Location(id=uuid.uuid4(), warehouse_id=wh.id, name="Loc3", short_code="L3")
    prod = Product(id=uuid.uuid4(), name="Item3", sku="ITM-003")
    db.add_all([wh, loc, prod])
    await db.flush()

    await adjust_stock(db, prod.id, loc.id, delta=Decimal("5"))
    with pytest.raises(HTTPException) as exc_info:
        await adjust_stock(db, prod.id, loc.id, delta=Decimal("-10"))
    assert exc_info.value.status_code == 400
