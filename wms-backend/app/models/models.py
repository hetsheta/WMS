from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OperationStatus(str, enum.Enum):
    draft = "draft"
    validated = "validated"
    ready = "ready"
    done = "done"
    cancelled = "cancelled"


class OperationType(str, enum.Enum):
    receipt = "receipt"
    delivery = "delivery"
    internal = "internal"
    adjustment = "adjustment"


class MoveState(str, enum.Enum):
    draft = "draft"
    done = "done"
    cancelled = "cancelled"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    operations: Mapped[List["Operation"]] = relationship(back_populates="created_by_user")
    warehouses: Mapped[List["Warehouse"]] = relationship(back_populates="owner")
    products: Mapped[List["Product"]] = relationship(back_populates="owner")


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_code: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    owner: Mapped[Optional["User"]] = relationship(back_populates="warehouses")
    locations: Mapped[List["Location"]] = relationship(back_populates="warehouse")

    __table_args__ = (UniqueConstraint("created_by", "short_code", name="uq_warehouse_short_code_per_user"),)


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    warehouse_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_code: Mapped[str] = mapped_column(String(20), nullable=False)
    barcode: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    warehouse: Mapped["Warehouse"] = relationship(back_populates="locations")
    stock_items: Mapped[List["StockItem"]] = relationship(back_populates="location")

    __table_args__ = (
        UniqueConstraint("warehouse_id", "short_code", name="uq_location_code_per_warehouse"),
        Index("ix_location_warehouse", "warehouse_id"),
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    unit_of_measure: Mapped[str] = mapped_column(String(50), default="unit")
    cost_price: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("0"))
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    owner: Mapped[Optional["User"]] = relationship(back_populates="products")
    stock_items: Mapped[List["StockItem"]] = relationship(back_populates="product")
    move_lines: Mapped[List["MoveLine"]] = relationship(back_populates="product")

    __table_args__ = (UniqueConstraint("created_by", "sku", name="uq_product_sku_per_user"),)


class StockItem(Base):
    __tablename__ = "stock_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), nullable=False)
    location_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("locations.id"), nullable=False)
    on_hand: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("0"))
    reserved: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("0"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    product: Mapped["Product"] = relationship(back_populates="stock_items")
    location: Mapped["Location"] = relationship(back_populates="stock_items")

    @property
    def free_to_use(self) -> Decimal:
        return self.on_hand - self.reserved

    __table_args__ = (
        UniqueConstraint("product_id", "location_id", name="uq_stock_product_location"),
        Index("ix_stock_product", "product_id"),
        Index("ix_stock_location", "location_id"),
    )


class Operation(Base):
    __tablename__ = "operations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    operation_type: Mapped[OperationType] = mapped_column(SAEnum(OperationType), nullable=False)
    status: Mapped[OperationStatus] = mapped_column(SAEnum(OperationStatus), nullable=False, default=OperationStatus.draft)
    warehouse_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    partner_name: Mapped[Optional[str]] = mapped_column(String(255))
    external_reference: Mapped[Optional[str]] = mapped_column(String(100))
    responsible_name: Mapped[Optional[str]] = mapped_column(String(255))
    scheduled_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    effective_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    warehouse: Mapped["Warehouse"] = relationship()
    created_by_user: Mapped["User"] = relationship(back_populates="operations")
    move_lines: Mapped[List["MoveLine"]] = relationship(back_populates="operation", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_operation_type_status", "operation_type", "status"),
        Index("ix_operation_warehouse", "warehouse_id"),
    )


class MoveLine(Base):
    __tablename__ = "move_lines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("operations.id"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), nullable=False)
    location_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("locations.id"), nullable=False)
    dest_location_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("locations.id"))
    state: Mapped[MoveState] = mapped_column(SAEnum(MoveState), default=MoveState.draft, nullable=False)
    qty_demand: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    qty_done: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("0"))
    unit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    done_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    operation: Mapped["Operation"] = relationship(back_populates="move_lines")
    product: Mapped["Product"] = relationship(back_populates="move_lines")
    location: Mapped["Location"] = relationship(foreign_keys=[location_id])
    dest_location: Mapped[Optional["Location"]] = relationship(foreign_keys=[dest_location_id])

    __table_args__ = (
        Index("ix_moveline_operation", "operation_id"),
        Index("ix_moveline_product", "product_id"),
    )
