from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "wms",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.jobs"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "daily-stock-check": {
            "task": "app.tasks.jobs.daily_stock_check",
            "schedule": 86400.0,  # every 24 hours
        },
    },
)
