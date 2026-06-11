from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import structlog

from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="app.workers.reminder_tasks.send_upcoming_reminders")
def send_upcoming_reminders() -> None:
    asyncio.run(_send_upcoming_reminders_async())


async def _send_upcoming_reminders_async() -> None:
    from app.core.database import AsyncSessionFactory
    from app.infrastructure.database.repositories.reservation_repository import (
        ReservationRepositoryImpl,
    )
    from app.workers.notification_tasks import send_reminder_task

    async with AsyncSessionFactory() as session:
        repo = ReservationRepositoryImpl(session)
        now = datetime.now(UTC)

        for hours_before in [24, 1]:
            remind_at = now + timedelta(hours=hours_before)
            reservations = await repo.get_upcoming_reminders(remind_at, window_minutes=15)
            for reservation in reservations:
                send_reminder_task.delay(
                    reservation_id=str(reservation.id),
                    customer_email="customer@example.com",  # fetch from user repo in production
                    customer_name="Customer",
                    resource_name="Resource",
                    start_time=reservation.time_slot.start.isoformat(),
                    hours_before=hours_before,
                )
            logger.info(
                "reminders_queued",
                hours_before=hours_before,
                count=len(reservations),
            )


@celery_app.task(name="app.workers.reminder_tasks.cleanup_expired_data")
def cleanup_expired_data() -> None:
    logger.info("cleanup_expired_data_started")


@celery_app.task(name="app.workers.reminder_tasks.auto_complete_past_reservations")
def auto_complete_past_reservations() -> None:
    asyncio.run(_auto_complete_async())


async def _auto_complete_async() -> None:
    from app.core.database import AsyncSessionFactory
    from app.domain.entities.reservation import ReservationStatus
    from app.infrastructure.database.models.reservation_model import ReservationModel
    from sqlalchemy import update
    from datetime import UTC

    now = datetime.now(UTC)
    async with AsyncSessionFactory() as session:
        await session.execute(
            update(ReservationModel)
            .where(
                ReservationModel.status == ReservationStatus.CONFIRMED.value,
                ReservationModel.end_time < now,
                ReservationModel.deleted_at.is_(None),
            )
            .values(
                status=ReservationStatus.COMPLETED.value,
                updated_at=now,
            )
        )
        await session.commit()
    logger.info("auto_complete_past_reservations_done")
