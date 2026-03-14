# WMS

Warehouse Management System monorepo with a React frontend and FastAPI backend.

## Repo Layout

```text
.
|- wms-frontend/   Vite + React app
|- wms-backend/    FastAPI + PostgreSQL + Alembic + Redis + Celery
```

## Stack

- Frontend: React, Vite, React Router, React Query, Tailwind CSS
- Backend: FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, Redis, Celery
- Dev environment: Docker Compose

## Quick Start

### 1. Backend

```powershell
cd wms-backend
docker compose up -d --build
docker compose exec api alembic upgrade head
```

Backend API:

- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 2. Frontend

```powershell
cd wms-frontend
npm install
npm run dev
```

Frontend app:

- `http://localhost:5173`

## Environment Files

- Backend template: `wms-backend/.env.example`
- Frontend template: `wms-frontend/.env.example`

Do not commit real `.env` files or secrets.

## Main Areas

- Authentication and JWT login
- Warehouses and locations
- Product catalog
- Stock tracking
- Operations workflow: draft -> validated -> ready -> done
- Move history and dashboard metrics

## Notes

- The root repo is intentionally lightweight.
- Detailed backend setup lives in `wms-backend/README.md`.
- Frontend-specific scripts and dependencies live in `wms-frontend/package.json`.
