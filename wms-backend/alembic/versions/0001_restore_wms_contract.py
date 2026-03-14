"""restore wms contract fields

Revision ID: 0001_restore_wms_contract
Revises:
Create Date: 2026-03-14 19:30:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_restore_wms_contract"
down_revision = None
branch_labels = None
depends_on = None


operation_type_enum = postgresql.ENUM(
    "receipt",
    "delivery",
    "internal",
    "adjustment",
    name="operationtype",
    create_type=False,
)

operation_status_enum = postgresql.ENUM(
    "draft",
    "validated",
    "ready",
    "done",
    "cancelled",
    name="operationstatus",
    create_type=False,
)

move_state_enum = postgresql.ENUM(
    "draft",
    "done",
    "cancelled",
    name="movestate",
    create_type=False,
)


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    operation_type_enum.create(bind, checkfirst=True)
    operation_status_enum.create(bind, checkfirst=True)
    move_state_enum.create(bind, checkfirst=True)

    if not _has_table(inspector, "users"):
        op.create_table(
            "users",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("hashed_password", sa.String(length=255), nullable=False),
            sa.Column("full_name", sa.String(length=255), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_users_email", "users", ["email"], unique=True)

    if not _has_table(inspector, "warehouses"):
        op.create_table(
            "warehouses",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("short_code", sa.String(length=20), nullable=False),
            sa.Column("address", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("short_code", name="warehouses_short_code_key"),
        )

    if not _has_table(inspector, "locations"):
        op.create_table(
            "locations",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("short_code", sa.String(length=20), nullable=False),
            sa.Column("barcode", sa.String(length=100), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("barcode"),
            sa.UniqueConstraint("warehouse_id", "short_code", name="uq_location_code_per_warehouse"),
        )
        op.create_index("ix_location_warehouse", "locations", ["warehouse_id"], unique=False)

    if not _has_table(inspector, "products"):
        op.create_table(
            "products",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("sku", sa.String(length=100), nullable=False),
            sa.Column("category", sa.String(length=100), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("unit_of_measure", sa.String(length=50), nullable=False, server_default=sa.text("'unit'")),
            sa.Column("cost_price", sa.Numeric(12, 4), nullable=False, server_default=sa.text("0")),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("sku", name="products_sku_key"),
        )
        op.create_index("ix_products_sku", "products", ["sku"], unique=False)

    if not _has_table(inspector, "stock_items"):
        op.create_table(
            "stock_items",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("on_hand", sa.Numeric(12, 4), nullable=False, server_default=sa.text("0")),
            sa.Column("reserved", sa.Numeric(12, 4), nullable=False, server_default=sa.text("0")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("product_id", "location_id", name="uq_stock_product_location"),
        )
        op.create_index("ix_stock_location", "stock_items", ["location_id"], unique=False)
        op.create_index("ix_stock_product", "stock_items", ["product_id"], unique=False)

    if not _has_table(inspector, "operations"):
        op.create_table(
            "operations",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("reference", sa.String(length=100), nullable=False),
            sa.Column("operation_type", operation_type_enum, nullable=False),
            sa.Column("status", operation_status_enum, nullable=False, server_default=sa.text("'draft'")),
            sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("partner_name", sa.String(length=255), nullable=True),
            sa.Column("external_reference", sa.String(length=100), nullable=True),
            sa.Column("responsible_name", sa.String(length=255), nullable=True),
            sa.Column("scheduled_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("effective_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_operation_type_status", "operations", ["operation_type", "status"], unique=False)
        op.create_index("ix_operation_warehouse", "operations", ["warehouse_id"], unique=False)
        op.create_index("ix_operations_reference", "operations", ["reference"], unique=True)

    if not _has_table(inspector, "move_lines"):
        op.create_table(
            "move_lines",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("operation_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("dest_location_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("state", move_state_enum, nullable=False, server_default=sa.text("'draft'")),
            sa.Column("qty_demand", sa.Numeric(12, 4), nullable=False),
            sa.Column("qty_done", sa.Numeric(12, 4), nullable=False, server_default=sa.text("0")),
            sa.Column("unit_price", sa.Numeric(12, 4), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("done_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["dest_location_id"], ["locations.id"], name="fk_move_lines_dest_location_id_locations"),
            sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
            sa.ForeignKeyConstraint(["operation_id"], ["operations.id"]),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_moveline_operation", "move_lines", ["operation_id"], unique=False)
        op.create_index("ix_moveline_product", "move_lines", ["product_id"], unique=False)

    inspector = sa.inspect(bind)

    if _has_table(inspector, "operations"):
        if not _has_column(inspector, "operations", "partner_name"):
            op.add_column("operations", sa.Column("partner_name", sa.String(length=255), nullable=True))
        if not _has_column(inspector, "operations", "external_reference"):
            op.add_column("operations", sa.Column("external_reference", sa.String(length=100), nullable=True))
        if not _has_column(inspector, "operations", "responsible_name"):
            op.add_column("operations", sa.Column("responsible_name", sa.String(length=255), nullable=True))

    if _has_table(inspector, "products") and not _has_column(inspector, "products", "category"):
        op.add_column("products", sa.Column("category", sa.String(length=100), nullable=True))

    if _has_table(inspector, "move_lines") and not _has_column(inspector, "move_lines", "dest_location_id"):
        op.add_column("move_lines", sa.Column("dest_location_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(
            "fk_move_lines_dest_location_id_locations",
            "move_lines",
            "locations",
            ["dest_location_id"],
            ["id"],
        )


def downgrade() -> None:
    op.drop_table("move_lines")
    op.drop_table("operations")
    op.drop_table("stock_items")
    op.drop_table("products")
    op.drop_table("locations")
    op.drop_table("warehouses")
    op.drop_table("users")

    bind = op.get_bind()
    move_state_enum.drop(bind, checkfirst=True)
    operation_status_enum.drop(bind, checkfirst=True)
    operation_type_enum.drop(bind, checkfirst=True)
