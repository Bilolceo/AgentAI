"""Celery application (reminders, async ingest). Used post-MVP."""
from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "callcenter",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
celery_app.conf.task_track_started = True
celery_app.autodiscover_tasks(["app.workers"])
