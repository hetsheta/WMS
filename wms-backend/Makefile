.PHONY: dev stop migrate migrate-new test lint fmt shell

dev:
	docker compose up --build

stop:
	docker compose down

migrate:
	alembic upgrade head

migrate-new:
	alembic revision --autogenerate -m "$(msg)"

test:
	pytest --cov=app --cov-report=term-missing -v

lint:
	ruff check .

fmt:
	ruff format .

shell:
	docker compose exec api bash

seed:
	python scripts/seed.py
