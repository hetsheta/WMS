import uuid
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import (
    Location,
    MoveLine,
    MoveState,
    Operation,
    OperationStatus,
    OperationType,
    Product,
    StockItem,
    Warehouse,
)
from app.schemas.schemas import OperationCreate
from app.services.stock import adjust_stock


async def _next_reference(db: AsyncSession, op_type: OperationType, user_id: UUID) -> str:
    prefix_map = {
        OperationType.receipt: "RCP",
        OperationType.delivery: "DLV",
        OperationType.internal: "TRF",
        OperationType.adjustment: "ADJ",
    }
    count = await db.scalar(
        select(func.count()).where(Operation.operation_type == op_type, Operation.created_by == user_id)
    )
    candidate_number = (count or 0) + 1

    while True:
        candidate = f"{prefix_map[op_type]}/{candidate_number:05d}"
        exists = await db.scalar(select(Operation.id).where(Operation.reference == candidate))
        if not exists:
            return candidate
        candidate_number += 1


def _operation_query():
    return select(Operation).options(
        selectinload(Operation.move_lines).selectinload(MoveLine.product),
        selectinload(Operation.move_lines).selectinload(MoveLine.location),
        selectinload(Operation.move_lines).selectinload(MoveLine.dest_location),
    )


async def create_operation(db: AsyncSession, data: OperationCreate, user_id: UUID) -> Operation:
    warehouse = await db.scalar(
        select(Warehouse).where(Warehouse.id == data.warehouse_id, Warehouse.created_by == user_id)
    )
    if not warehouse or not warehouse.is_active:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    op = Operation(
        id=uuid.uuid4(),
        reference=await _next_reference(db, data.operation_type, user_id),
        operation_type=data.operation_type,
        status=OperationStatus.draft,
        warehouse_id=data.warehouse_id,
        created_by=user_id,
        partner_name=data.partner_name,
        external_reference=data.external_reference,
        responsible_name=data.responsible_name,
        scheduled_date=data.scheduled_date,
        notes=data.notes,
    )
    db.add(op)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Unable to create operation right now") from exc

    for line_data in data.lines:
        product = await db.scalar(
            select(Product).where(Product.id == line_data.product_id, Product.created_by == user_id)
        )
        if not product or not product.is_active:
            raise HTTPException(status_code=404, detail="Product not found")

        source_location = await db.scalar(
            select(Location)
            .join(Warehouse, Location.warehouse_id == Warehouse.id)
            .where(Location.id == line_data.location_id, Warehouse.created_by == user_id)
        )
        if not source_location or not source_location.is_active or source_location.warehouse_id != data.warehouse_id:
            raise HTTPException(status_code=400, detail="Source location is invalid for the selected warehouse")

        if line_data.dest_location_id:
            dest_location = await db.scalar(
                select(Location)
                .join(Warehouse, Location.warehouse_id == Warehouse.id)
                .where(Location.id == line_data.dest_location_id, Warehouse.created_by == user_id)
            )
            if not dest_location or not dest_location.is_active or dest_location.warehouse_id != data.warehouse_id:
                raise HTTPException(status_code=400, detail="Destination location is invalid for the selected warehouse")

        db.add(
            MoveLine(
                id=uuid.uuid4(),
                operation_id=op.id,
                product_id=line_data.product_id,
                location_id=line_data.location_id,
                dest_location_id=line_data.dest_location_id,
                qty_demand=line_data.qty_demand,
                unit_price=line_data.unit_price,
                state=MoveState.draft,
            )
        )

    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Unable to create operation right now") from exc
    await db.commit()
    return await get_operation(db, op.id, user_id)


async def get_operation(db: AsyncSession, operation_id: UUID, user_id: UUID) -> Operation:
    op = await db.scalar(_operation_query().where(Operation.id == operation_id, Operation.created_by == user_id))
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")
    return op


async def list_operations(
    db: AsyncSession,
    user_id: UUID,
    q: str | None = None,
    op_type: OperationType | None = None,
    status: OperationStatus | None = None,
    warehouse_id: UUID | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[Operation], int]:
    query = select(Operation).options(selectinload(Operation.move_lines)).where(Operation.created_by == user_id)
    if q:
        term = f"%{q}%"
        query = query.where(
            or_(
                Operation.reference.ilike(term),
                Operation.partner_name.ilike(term),
                Operation.external_reference.ilike(term),
                Operation.responsible_name.ilike(term),
            )
        )
    if op_type:
        query = query.where(Operation.operation_type == op_type)
    if status:
        query = query.where(Operation.status == status)
    if warehouse_id:
        query = query.where(Operation.warehouse_id == warehouse_id)

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    ops = await db.scalars(query.order_by(Operation.created_at.desc()).offset(skip).limit(limit))
    return list(ops.all()), total or 0


_TRANSITIONS = {
    OperationStatus.draft: {OperationStatus.validated, OperationStatus.cancelled},
    OperationStatus.validated: {OperationStatus.ready, OperationStatus.cancelled},
    OperationStatus.ready: {OperationStatus.done, OperationStatus.cancelled},
    OperationStatus.done: set(),
    OperationStatus.cancelled: set(),
}


def _assert_transition(current: OperationStatus, target: OperationStatus):
    if target not in _TRANSITIONS[current]:
        raise HTTPException(status_code=400, detail=f"Cannot transition from '{current}' to '{target}'")


async def validate_operation(db: AsyncSession, operation_id: UUID, user_id: UUID) -> Operation:
    op = await get_operation(db, operation_id, user_id)
    _assert_transition(op.status, OperationStatus.validated)
    op.status = OperationStatus.validated
    await db.commit()
    return await get_operation(db, operation_id, user_id)


async def mark_ready(db: AsyncSession, operation_id: UUID, user_id: UUID) -> Operation:
    op = await get_operation(db, operation_id, user_id)
    _assert_transition(op.status, OperationStatus.ready)
    op.status = OperationStatus.ready
    await db.commit()
    return await get_operation(db, operation_id, user_id)


async def confirm_operation(
    db: AsyncSession, operation_id: UUID, done_quantities: dict[UUID, Decimal], user_id: UUID
) -> Operation:
    op = await get_operation(db, operation_id, user_id)
    _assert_transition(op.status, OperationStatus.done)

    for line in op.move_lines:
        qty = done_quantities.get(line.id, line.qty_demand)
        if op.operation_type in {OperationType.receipt, OperationType.delivery, OperationType.internal} and qty < 0:
            raise HTTPException(status_code=400, detail="Done quantity cannot be negative")
        if op.operation_type == OperationType.adjustment and qty == 0:
            raise HTTPException(status_code=400, detail="Adjustment quantity cannot be zero")

        line.qty_done = qty
        line.state = MoveState.done
        line.done_at = datetime.now(timezone.utc)

        if op.operation_type == OperationType.receipt:
            await adjust_stock(db, line.product_id, line.location_id, delta=qty)
        elif op.operation_type == OperationType.delivery:
            await adjust_stock(db, line.product_id, line.location_id, delta=-qty)
        elif op.operation_type == OperationType.internal:
            if not line.dest_location_id:
                raise HTTPException(status_code=400, detail="Internal transfer line is missing a destination location")
            await adjust_stock(db, line.product_id, line.location_id, delta=-qty)
            await adjust_stock(db, line.product_id, line.dest_location_id, delta=qty)
        else:
            await adjust_stock(db, line.product_id, line.location_id, delta=qty)

    op.status = OperationStatus.done
    op.effective_date = datetime.now(timezone.utc)
    await db.commit()
    return await get_operation(db, operation_id, user_id)


async def cancel_operation(db: AsyncSession, operation_id: UUID, user_id: UUID) -> Operation:
    op = await get_operation(db, operation_id, user_id)
    _assert_transition(op.status, OperationStatus.cancelled)
    for line in op.move_lines:
        line.state = MoveState.cancelled
    op.status = OperationStatus.cancelled
    await db.commit()
    return await get_operation(db, operation_id, user_id)


async def get_dashboard_stats(db: AsyncSession, user_id: UUID) -> dict:
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    async def count(op_type: OperationType, *conditions) -> int:
        result = await db.scalar(
            select(func.count()).where(Operation.operation_type == op_type, Operation.created_by == user_id, *conditions)
        )
        return result or 0

    return {
        "total_products": await db.scalar(
            select(func.count()).select_from(Product).where(Product.created_by == user_id)
        ) or 0,
        "low_stock_items": await db.scalar(
            select(func.count())
            .select_from(StockItem)
            .join(Product, StockItem.product_id == Product.id)
            .where(Product.created_by == user_id, (StockItem.on_hand - StockItem.reserved) <= 10)
        ) or 0,
        "receipts_today": await count(OperationType.receipt, Operation.created_at >= today_start),
        "receipts_pending": await count(OperationType.receipt, Operation.status == OperationStatus.validated),
        "receipts_waiting": await count(OperationType.receipt, Operation.status == OperationStatus.ready),
        "deliveries_today": await count(OperationType.delivery, Operation.created_at >= today_start),
        "deliveries_pending": await count(OperationType.delivery, Operation.status == OperationStatus.validated),
        "deliveries_waiting": await count(OperationType.delivery, Operation.status == OperationStatus.ready),
        "internal_today": await count(OperationType.internal, Operation.created_at >= today_start),
        "internal_pending": await count(OperationType.internal, Operation.status == OperationStatus.validated),
        "internal_waiting": await count(OperationType.internal, Operation.status == OperationStatus.ready),
    }


async def list_move_history(
    db: AsyncSession,
    user_id: UUID,
    q: str | None = None,
    op_type: OperationType | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[MoveLine], int]:
    query = (
        select(MoveLine)
        .join(Operation, MoveLine.operation_id == Operation.id)
        .options(
            selectinload(MoveLine.operation),
            selectinload(MoveLine.product),
            selectinload(MoveLine.location),
            selectinload(MoveLine.dest_location),
        )
        .where(Operation.created_by == user_id)
    )
    if q:
        term = f"%{q}%"
        query = (
            query.join(Product, MoveLine.product_id == Product.id)
            .join(Location, MoveLine.location_id == Location.id)
            .where(
                or_(
                    Operation.reference.ilike(term),
                    Product.name.ilike(term),
                    Product.sku.ilike(term),
                    Location.name.ilike(term),
                )
            )
        )
    if op_type:
        query = query.where(Operation.operation_type == op_type)

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    rows = await db.scalars(query.order_by(func.coalesce(MoveLine.done_at, MoveLine.created_at).desc()).offset(skip).limit(limit))
    return list(rows.all()), total or 0
