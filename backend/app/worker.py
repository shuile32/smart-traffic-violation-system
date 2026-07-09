# app/worker.py
"""Celery 应用入口。运行：uv run celery -A app.worker worker --loglevel=info"""
from celery import Celery

from app.core.config import settings

app = Celery(
    "traffic_violation",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.report_task"],
)

app.conf.update(task_always_eager=False, task_serializer="json", accept_content=["json"])
