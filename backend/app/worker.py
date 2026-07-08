"""Celery Worker 入口

启动: celery -A app.worker worker --loglevel=info -P solo
"""

from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "traffic_violation",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.detect_objects_task",
        "app.tasks.ocr_plate_task",
        "app.tasks.evaluate_rule_task",
        "app.tasks.ai_review_task",
        "app.tasks.send_notification_task",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    task_track_started=True,
    task_time_limit=600,
    task_soft_time_limit=540,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=200,
)
