# Warehouse Management System

A production-ready WMS built with **FastAPI**, **PostgreSQL**, **SQLAlchemy 2**, **Alembic**, **Redis**, and **Celery**.

## Features

| Module | Description |
|---|---|
| Auth | JWT login/register with refresh tokens |
| Warehouses | Multi-warehouse with named locations |
| Products | SKU catalogue with cost price |
| Stock | On-hand / reserved / free-to-use per location |
| Receipts | Inbound operations (draft → validated → ready → done) |
| Deliveries | Outbound operations with stock deduction |
| Move History | Append-only audit trail via `move_lines` |
| Dashboard | Today's counts + pending/waiting stats |
| Tasks | Celery: PDF generation, notifications, nightly stock check |

---

## Project structure

```
wms/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/     # auth, warehouses, products, stock, operations, dashboard
│   │       └── router.py
│   ├── core/
│   │   ├── config.py          # pydantic-settings
│   │   └── security.py        # JWT, bcrypt
│   ├── db/
│   │   └── session.py         # async engine + session factory
│   ├── models/
│   │   └── models.py          # SQLAlchemy ORM (User, Warehouse, Location, Product, StockItem, Operation, MoveLine)
│   ├── schemas/
│   │   └── schemas.py         # Pydantic v2 request/response models
│   ├── services/
│   │   ├── auth.py
│   │   ├── stock.py           # SELECT FOR UPDATE race-safe adjustments
│   │   ├── operations.py      # State machine + stock moves
│   │   ├── warehouse.py
│   │   └── products.py
│   ├── tasks/
│   │   ├── celery_app.py
│   │   └── jobs.py            # PDF gen, notifications, nightly check
│   └── main.py
├── alembic/
│   ├── env.py                 # async migrations
│   └── versions/
├── tests/
│   ├── conftest.py            # async fixtures, test DB
│   ├── api/
│   │   ├── test_auth.py
│   │   └── test_operations.py
│   └── services/
│       └── test_stock.py
├── scripts/
│   └── seed.py
├── .github/workflows/ci.yml
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── alembic.ini
├── pyproject.toml
└── requirements.txt
```

---

## Quick start

### 1. Clone and configure

```bash
cp .env.example .env
# Edit .env if needed (defaults work out of the box with Docker)
```

### 2. Start the full stack

```bash
make dev
# Starts: api (port 8000), postgres (5432), redis (6379), celery worker
```

### 3. Run migrations

```bash
make migrate
```

### 4. Seed dev data

```bash
make seed
# Creates: admin@wms.local / admin1234, 1 warehouse, 5 locations, 5 products
```

### 5. Explore the API

- Swagger UI: http://localhost:8000/docs
- ReDoc:       http://localhost:8000/redoc
- Health:      http://localhost:8000/health

---

## Key API endpoints

### Auth
```
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
```

### Warehouses & Locations
```
GET  /api/v1/warehouses
POST /api/v1/warehouses
GET  /api/v1/warehouses/{id}
POST /api/v1/warehouses/{id}/locations
GET  /api/v1/warehouses/{id}/locations
```

### Products
```
GET  /api/v1/products?search=widget
POST /api/v1/products
GET  /api/v1/products/{id}
PATCH /api/v1/products/{id}
```

### Stock
```
GET  /api/v1/stock?warehouse_id=...&product_id=...
POST /api/v1/stock/adjust
```

### Operations (receipts & deliveries)
```
POST /api/v1/operations                          # create (type: receipt|delivery)
GET  /api/v1/operations?op_type=receipt&status=draft
GET  /api/v1/operations/{id}
POST /api/v1/operations/{id}/validate            # draft → validated
POST /api/v1/operations/{id}/ready               # validated → ready
POST /api/v1/operations/{id}/confirm             # ready → done  (applies stock moves)
POST /api/v1/operations/{id}/cancel
```

### Dashboard
```
GET  /api/v1/dashboard
```

---

## Operation state machine

```
draft ──► validated ──► ready ──► done
  └──────────────────────────► cancelled
```

Confirming a **receipt** adds to `stock_items.on_hand`.  
Confirming a **delivery** subtracts from `stock_items.on_hand` (raises 400 if insufficient).  
All moves are recorded as `move_lines` rows — never deleted.

---

## Stock safety

Stock updates use `SELECT FOR UPDATE` (row-level locking) inside a transaction:

```python
# services/stock.py
item = await get_stock_item(db, product_id, location_id, for_update=True)
```

This prevents two simultaneous deliveries from overdrawing the same stock row.

---

## Development commands

```bash
make dev            # start all services
make stop           # stop all services
make migrate        # apply pending migrations
make migrate-new msg="add_barcode_to_product"  # generate new migration
make test           # run pytest with coverage
make lint           # ruff check
make fmt            # ruff format
make seed           # seed dev data
make shell          # bash into the api container
```

---

## Running tests

```bash
# Requires a running Postgres instance (wms_test database)
make test

# Or directly:
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://wms:wms@localhost:5432/wms` | Async Postgres URL |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for cache + Celery |
| `SECRET_KEY` | — | JWT signing key (use `openssl rand -hex 32`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | JWT access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed frontend origins |
| `AWS_BUCKET_NAME` | `wms-attachments` | S3/R2 bucket for PDFs |
