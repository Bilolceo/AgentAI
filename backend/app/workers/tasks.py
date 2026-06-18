"""Celery tasks — reminders and async knowledge ingest (post-MVP).

These are thin wrappers; heavy lifting lives in the services. Kept as stubs so
the worker container has an entry point.
"""
from __future__ import annotations

from app.core.logging import get_logger
from app.workers.celery_app import celery_app

log = get_logger("workers")


@celery_app.task(name="send_reminder")
def send_reminder(to: str, body: str) -> None:
    # TODO: NotificationService orqali SMS/Telegram yuborish.
    log.info("send_reminder", to=to, body=body)


@celery_app.task(name="ingest_document")
def ingest_document_task(source: str, content: str, language: str | None = None) -> None:
    # TODO: embeddings yoqilgach RAG ingest'ni chaqirish.
    log.info("ingest_document_task", source=source, language=language)
