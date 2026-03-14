"""
Seed script — populates the DB with a warehouse, locations, products and an admin user.
Run with: python scripts/seed.py
"""
import asyncio
import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.core.security import hash_password
from app.db.session import Base
from app.models.models import User, Warehouse, Location, Product

engine = create_async_engine(settings.DATABASE_URL, echo=True)
Session = async_sessionmaker(bind=engine, expire_on_commit=False)


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with Session() as db:
        # Admin user
        admin = User(
            id=uuid.uuid4(),
            email="admin@wms.local",
            hashed_password=hash_password("admin1234"),
            full_name="Admin User",
            is_active=True,
            is_superuser=True,
        )
        db.add(admin)

        # Warehouse
        wh = Warehouse(
            id=uuid.uuid4(),
            name="Main Warehouse",
            short_code="MWH",
            address="123 Logistics Park, Surat, GJ 395001",
        )
        db.add(wh)
        await db.flush()

        # Locations
        locations = [
            Location(id=uuid.uuid4(), warehouse_id=wh.id, name="Receiving Bay", short_code="RCV", barcode="LOC-RCV"),
            Location(id=uuid.uuid4(), warehouse_id=wh.id, name="Shelf A1",      short_code="A1",  barcode="LOC-A01"),
            Location(id=uuid.uuid4(), warehouse_id=wh.id, name="Shelf A2",      short_code="A2",  barcode="LOC-A02"),
            Location(id=uuid.uuid4(), warehouse_id=wh.id, name="Shelf B1",      short_code="B1",  barcode="LOC-B01"),
            Location(id=uuid.uuid4(), warehouse_id=wh.id, name="Dispatch Bay",  short_code="DSP", barcode="LOC-DSP"),
        ]
        db.add_all(locations)

        # Products
        products = [
            Product(id=uuid.uuid4(), name="Widget A",    sku="WGT-A001", unit_of_measure="pcs", cost_price=Decimal("12.50")),
            Product(id=uuid.uuid4(), name="Widget B",    sku="WGT-B002", unit_of_measure="pcs", cost_price=Decimal("8.00")),
            Product(id=uuid.uuid4(), name="Gadget Pro",  sku="GDG-P003", unit_of_measure="pcs", cost_price=Decimal("45.99")),
            Product(id=uuid.uuid4(), name="Cable 2m",    sku="CBL-2004", unit_of_measure="pcs", cost_price=Decimal("3.25")),
            Product(id=uuid.uuid4(), name="Box (small)", sku="BOX-S005", unit_of_measure="box", cost_price=Decimal("1.10")),
        ]
        db.add_all(products)

        await db.commit()

    print("\n✓ Seed complete")
    print("  Admin login → admin@wms.local / admin1234")
    print(f"  Warehouse   → Main Warehouse ({wh.short_code})")
    print(f"  Locations   → {len(locations)} created")
    print(f"  Products    → {len(products)} created")


if __name__ == "__main__":
    asyncio.run(seed())
