from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.deps import current_user
from app.models.models import User
from app.schemas.schemas import ProductCreate, ProductUpdate, ProductOut
from app.services import products as prod_svc

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=ProductOut, status_code=201)
async def create(data: ProductCreate, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return await prod_svc.create_product(db, data, user.id)


@router.get("", response_model=dict)
async def list_all(
    search: str | None = Query(default=None),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    items, total = await prod_svc.list_products(db, user.id, search, skip, limit)
    return {"total": total, "page": skip // limit + 1, "size": limit, "items": [ProductOut.model_validate(p) for p in items]}


@router.get("/{product_id}", response_model=ProductOut)
async def get(product_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return await prod_svc.get_product(db, product_id, user.id)


@router.patch("/{product_id}", response_model=ProductOut)
async def update(product_id: UUID, data: ProductUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return await prod_svc.update_product(db, product_id, data, user.id)
