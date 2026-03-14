import uuid
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Product
from app.schemas.schemas import ProductCreate, ProductUpdate


async def create_product(db: AsyncSession, data: ProductCreate, user_id: UUID) -> Product:
    existing = await db.scalar(select(Product).where(Product.sku == data.sku, Product.created_by == user_id))
    if existing:
        raise HTTPException(status_code=400, detail="SKU already exists")
    product = Product(id=uuid.uuid4(), created_by=user_id, **data.model_dump())
    db.add(product)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail="SKU already exists") from exc
    return product


async def get_product(db: AsyncSession, product_id: UUID, user_id: UUID) -> Product:
    product = await db.scalar(select(Product).where(Product.id == product_id, Product.created_by == user_id))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


async def list_products(
    db: AsyncSession, user_id: UUID, search: str | None = None, skip: int = 0, limit: int = 50
) -> tuple[list[Product], int]:
    query = select(Product).where(Product.created_by == user_id)
    if search:
        query = query.where(
            Product.name.ilike(f"%{search}%")
            | Product.sku.ilike(f"%{search}%")
            | Product.category.ilike(f"%{search}%")
        )
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    products = await db.scalars(query.offset(skip).limit(limit))
    return list(products.all()), total or 0


async def update_product(db: AsyncSession, product_id: UUID, data: ProductUpdate, user_id: UUID) -> Product:
    product = await get_product(db, product_id, user_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(product, field, value)
    await db.flush()
    return product
