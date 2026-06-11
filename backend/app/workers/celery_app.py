from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings
import app.infrastructure.database.models  # noqa: F401 — registers all ORM mappers

celery_app = Celery(
    "reservation_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.notification_tasks",
        "app.workers.reminder_tasks",
        "app.workers.report_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_max_retries=3,
    task_default_retry_delay=60,
    result_expires=3600,
    worker_send_task_events=True,
    task_send_sent_event=True,
)

celery_app.conf.beat_schedule = {
    "send-reservation-reminders-hourly": {
        "task": "app.workers.reminder_tasks.send_upcoming_reminders",
        "schedule": crontab(minute=0),
    },
    "cleanup-expired-tokens-daily": {
        "task": "app.workers.reminder_tasks.cleanup_expired_data",
        "schedule": crontab(hour=2, minute=0),
    },
    "complete-past-reservations-hourly": {
        "task": "app.workers.reminder_tasks.auto_complete_past_reservations",
        "schedule": crontab(minute=30),
    },
}
