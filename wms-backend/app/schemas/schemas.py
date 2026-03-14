from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.models.models import MoveState, OperationStatus, OperationType


class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: datetime


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: UUID
    email: str
    full_name: str
    is_active: bool
    is_superuser: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class WarehouseCreate(BaseModel):
    name: str = Field(max_length=255)
    short_code: str = Field(max_length=20)
    address: Optional[str] = None

    @field_validator("name", "short_code", mode="before")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        if isinstance(value, str):
            value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank")
        return value

    @field_validator("address", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if isinstance(value, str):
            value = value.strip()
        return value or None


class WarehouseUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("name", "address", mode="before")
    @classmethod
    def normalize_update_text(cls, value: Optional[str]) -> Optional[str]:
        if isinstance(value, str):
            value = value.strip()
        return value or None


class WarehouseOut(BaseModel):
    id: UUID
    name: str
    short_code: str
    address: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class LocationCreate(BaseModel):
    name: str = Field(max_length=255)
    short_code: str = Field(max_length=20)
    barcode: Optional[str] = None

    @field_validator("name", "short_code", mode="before")
    @classmethod
    def normalize_location_text(cls, value: str) -> str:
        if isinstance(value, str):
            value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank")
        return value

    @field_validator("barcode", mode="before")
    @classmethod
    def normalize_barcode(cls, value: Optional[str]) -> Optional[str]:
        if isinstance(value, str):
            value = value.strip()
        return value or None


class LocationOut(BaseModel):
    id: UUID
    warehouse_id: UUID
    name: str
    short_code: str
    barcode: Optional[str]
    is_active: bool

    model_config = {"from_attributes": True}


class ProductCreate(BaseModel):
    name: str = Field(max_length=255)
    sku: str = Field(max_length=100)
    category: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None
    unit_of_measure: str = "unit"
    cost_price: Decimal = Field(default=Decimal("0"), ge=0)

    @field_validator("name", "sku", "unit_of_measure", mode="before")
    @classmethod
    def normalize_product_text(cls, value: str) -> str:
        if isinstance(value, str):
            value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank")
        return value

    @field_validator("category", "description", mode="before")
    @classmethod
    def normalize_product_description(cls, value: Optional[str]) -> Optional[str]:
        if isinstance(value, str):
            value = value.strip()
        return value or None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    cost_price: Optional[Decimal] = Field(default=None, ge=0)
    is_active: Optional[bool] = None

    @field_validator("name", "category", "description", mode="before")
    @classmethod
    def normalize_product_update_text(cls, value: Optional[str]) -> Optional[str]:
        if isinstance(value, str):
            value = value.strip()
        return value or None


class ProductOut(BaseModel):
    id: UUID
    name: str
    sku: str
    category: Optional[str]
    description: Optional[str]
    unit_of_measure: str
    cost_price: Decimal
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductSummary(BaseModel):
    id: UUID
    name: str
    sku: str

    model_config = {"from_attributes": True}


class LocationSummary(BaseModel):
    id: UUID
    warehouse_id: UUID
    name: str
    short_code: str
    barcode: Optional[str]

    model_config = {"from_attributes": True}


class StockItemOut(BaseModel):
    id: UUID
    product_id: UUID
    location_id: UUID
    on_hand: Decimal
    reserved: Decimal
    free_to_use: Decimal
    updated_at: datetime
    product: Optional[ProductSummary] = None
    location: Optional[LocationSummary] = None

    model_config = {"from_attributes": True}


class StockAdjust(BaseModel):
    product_id: UUID
    location_id: UUID
    quantity: Decimal = Field(description="Positive to add, negative to remove")
    reason: Optional[str] = None


class MoveLineCreate(BaseModel):
    product_id: UUID
    location_id: UUID
    dest_location_id: Optional[UUID] = None
    qty_demand: Decimal
    unit_price: Optional[Decimal] = None


class MoveLineUpdate(BaseModel):
    qty_done: Optional[Decimal] = Field(default=None, ge=0)


class MoveLineOut(BaseModel):
    id: UUID
    operation_id: UUID
    product_id: UUID
    location_id: UUID
    dest_location_id: Optional[UUID]
    state: MoveState
    qty_demand: Decimal
    qty_done: Decimal
    unit_price: Optional[Decimal]
    created_at: datetime
    done_at: Optional[datetime]
    product: Optional[ProductSummary] = None
    location: Optional[LocationSummary] = None
    dest_location: Optional[LocationSummary] = None

    model_config = {"from_attributes": True}


class OperationCreate(BaseModel):
    operation_type: OperationType
    warehouse_id: UUID
    partner_name: Optional[str] = Field(default=None, max_length=255)
    external_reference: Optional[str] = Field(default=None, max_length=100)
    responsible_name: Optional[str] = Field(default=None, max_length=255)
    scheduled_date: Optional[datetime] = None
    notes: Optional[str] = None
    lines: List[MoveLineCreate] = Field(default_factory=list)

    @field_validator("partner_name", "external_reference", "responsible_name", "notes", mode="before")
    @classmethod
    def normalize_operation_text(cls, value: Optional[str]) -> Optional[str]:
        if isinstance(value, str):
            value = value.strip()
        return value or None

    @model_validator(mode="after")
    def validate_lines(self):
        for line in self.lines:
            if self.operation_type in {OperationType.receipt, OperationType.delivery, OperationType.internal} and line.qty_demand <= 0:
                raise ValueError("Quantity must be greater than zero")
            if self.operation_type == OperationType.adjustment and line.qty_demand == 0:
                raise ValueError("Adjustment quantity cannot be zero")
            if self.operation_type == OperationType.internal and not line.dest_location_id:
                raise ValueError("Internal transfers require a destination location")
            if self.operation_type != OperationType.internal and line.dest_location_id:
                raise ValueError("Destination location is only supported for internal transfers")
        return self


class OperationUpdate(BaseModel):
    partner_name: Optional[str] = None
    external_reference: Optional[str] = None
    responsible_name: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    notes: Optional[str] = None


class OperationOut(BaseModel):
    id: UUID
    reference: str
    operation_type: OperationType
    status: OperationStatus
    warehouse_id: UUID
    created_by: UUID
    partner_name: Optional[str]
    external_reference: Optional[str]
    responsible_name: Optional[str]
    scheduled_date: Optional[datetime]
    effective_date: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    move_lines: List[MoveLineOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    total_products: int
    low_stock_items: int
    receipts_today: int
    receipts_pending: int
    receipts_waiting: int
    deliveries_today: int
    deliveries_pending: int
    deliveries_waiting: int
    internal_today: int
    internal_pending: int
    internal_waiting: int


class MoveHistoryItem(BaseModel):
    id: UUID
    reference: str
    operation_type: OperationType
    product_id: UUID
    location_id: UUID
    dest_location_id: Optional[UUID]
    qty_done: Decimal
    created_at: datetime
    done_at: Optional[datetime]
    product: Optional[ProductSummary] = None
    location: Optional[LocationSummary] = None
    dest_location: Optional[LocationSummary] = None


class MoveHistoryResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[MoveHistoryItem]


class PaginatedResponse(BaseModel):
    total: int
    page: int
    size: int
    items: list
