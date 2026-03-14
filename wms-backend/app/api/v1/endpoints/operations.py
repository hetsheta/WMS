from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user
from app.db.session import get_db
from app.models.models import OperationStatus, OperationType, User
from app.schemas.schemas import MoveHistoryItem, MoveHistoryResponse, OperationCreate, OperationOut
from app.services import operations as ops_svc

router = APIRouter(prefix="/operations", tags=["operations"])


@router.post("", response_model=OperationOut, status_code=201)
async def create(data: OperationCreate, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return await ops_svc.create_operation(db, data, user.id)


@router.get("/history", response_model=MoveHistoryResponse)
async def history(
    q: str | None = Query(default=None),
    op_type: OperationType | None = Query(default=None),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    items, total = await ops_svc.list_move_history(db, user.id, q, op_type, skip, limit)
    return MoveHistoryResponse(
        total=total,
        page=skip // limit + 1,
        size=limit,
        items=[
            MoveHistoryItem(
                id=item.id,
                reference=item.operation.reference,
                operation_type=item.operation.operation_type,
                product_id=item.product_id,
                location_id=item.location_id,
                dest_location_id=item.dest_location_id,
                qty_done=item.qty_done,
                created_at=item.created_at,
                done_at=item.done_at,
                product=item.product,
                location=item.location,
                dest_location=item.dest_location,
            )
            for item in items
        ],
    )


@router.get("", response_model=dict)
async def list_all(
    q: str | None = Query(default=None),
    op_type: OperationType | None = Query(default=None),
    status: OperationStatus | None = Query(default=None),
    warehouse_id: UUID | None = Query(default=None),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    items, total = await ops_svc.list_operations(db, user.id, q, op_type, status, warehouse_id, skip, limit)
    return {
        "total": total,
        "page": skip // limit + 1,
        "size": limit,
        "items": [OperationOut.model_validate(op) for op in items],
    }


@router.get("/{operation_id}", response_model=OperationOut)
async def get(operation_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return await ops_svc.get_operation(db, operation_id, user.id)


@router.post("/{operation_id}/validate", response_model=OperationOut)
async def validate(operation_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return await ops_svc.validate_operation(db, operation_id, user.id)


@router.post("/{operation_id}/ready", response_model=OperationOut)
async def mark_ready(operation_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return await ops_svc.mark_ready(db, operation_id, user.id)


@router.post("/{operation_id}/confirm", response_model=OperationOut)
async def confirm(
    operation_id: UUID,
    done_quantities: dict[str, Decimal],
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    qty_map = {UUID(key): value for key, value in done_quantities.items()}
    return await ops_svc.confirm_operation(db, operation_id, qty_map, user.id)


@router.post("/{operation_id}/cancel", response_model=OperationOut)
async def cancel(operation_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return await ops_svc.cancel_operation(db, operation_id, user.id)
