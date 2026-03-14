"""scope warehouses and products per user

Revision ID: 0002_scope_data_per_user
Revises: 0001_restore_wms_contract
Create Date: 2026-03-14 21:15:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0002_scope_data_per_user"
down_revision = "0001_restore_wms_contract"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("warehouses", sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("products", sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_warehouses_created_by", "warehouses", ["created_by"], unique=False)
    op.create_index("ix_products_created_by", "products", ["created_by"], unique=False)
    op.create_foreign_key("fk_warehouses_created_by_users", "warehouses", "users", ["created_by"], ["id"])
    op.create_foreign_key("fk_products_created_by_users", "products", "users", ["created_by"], ["id"])

    op.execute(
        """
        WITH first_user AS (
            SELECT id
            FROM users
            ORDER BY created_at ASC, id ASC
            LIMIT 1
        )
        UPDATE warehouses
        SET created_by = (SELECT id FROM first_user)
        WHERE created_by IS NULL
        """
    )

    op.execute(
        """
        WITH ranked AS (
            SELECT
                id,
                short_code,
                ROW_NUMBER() OVER (
                    PARTITION BY created_by, short_code
                    ORDER BY created_at ASC, id ASC
                ) AS rn
            FROM warehouses
            WHERE created_by IS NOT NULL
        )
        UPDATE warehouses AS w
        SET short_code = LEFT(r.short_code || '-' || r.rn::text, 20)
        FROM ranked AS r
        WHERE w.id = r.id
          AND r.rn > 1
        """
    )
    op.execute(
        """
        WITH ranked AS (
            SELECT
                id,
                sku,
                ROW_NUMBER() OVER (
                    PARTITION BY created_by, sku
                    ORDER BY created_at ASC, id ASC
                ) AS rn
            FROM products
            WHERE created_by IS NOT NULL
        )
        UPDATE products AS p
        SET sku = LEFT(r.sku || '-' || r.rn::text, 100)
        FROM ranked AS r
        WHERE p.id = r.id
          AND r.rn > 1
        """
    )

    op.execute("ALTER TABLE warehouses DROP CONSTRAINT IF EXISTS warehouses_short_code_key")
    op.execute("ALTER TABLE products DROP CONSTRAINT IF EXISTS products_sku_key")
    op.create_unique_constraint("uq_warehouse_short_code_per_user", "warehouses", ["created_by", "short_code"])
    op.create_unique_constraint("uq_product_sku_per_user", "products", ["created_by", "sku"])
    op.execute(
        """
        WITH first_user AS (
            SELECT id
            FROM users
            ORDER BY created_at ASC, id ASC
            LIMIT 1
        )
        UPDATE products
        SET created_by = (SELECT id FROM first_user)
        WHERE created_by IS NULL
        """
    )


def downgrade() -> None:
    op.drop_constraint("uq_product_sku_per_user", "products", type_="unique")
    op.drop_constraint("uq_warehouse_short_code_per_user", "warehouses", type_="unique")
    op.create_unique_constraint("products_sku_key", "products", ["sku"])
    op.create_unique_constraint("warehouses_short_code_key", "warehouses", ["short_code"])
    op.drop_constraint("fk_products_created_by_users", "products", type_="foreignkey")
    op.drop_constraint("fk_warehouses_created_by_users", "warehouses", type_="foreignkey")
    op.drop_index("ix_products_created_by", table_name="products")
    op.drop_index("ix_warehouses_created_by", table_name="warehouses")
    op.drop_column("products", "created_by")
    op.drop_column("warehouses", "created_by")
