from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta, timezone

from redis.asyncio import Redis

from app.application.dtos.reservation_dtos import (
    AvailableSlotResponse,
    CancelReservationRequest,
    CreateReservationRequest,
    ReservationListResponse,
    ReservationResponse,
    UpdateReservationRequest,
)
from app.core.logging import get_logger
from app.core.redis_client import RedisKeys
from app.domain.entities.reservation import Reservation, ReservationStatus
from app.domain.entities.user import UserRole
from app.domain.value_objects.time_slot import TimeSlot
from app.infrastructure.database.repositories.reservation_repository import (
    ReservationRepositoryImpl,
)
from app.infrastructure.database.repositories.resource_repository import ResourceRepositoryImpl
from app.infrastructure.database.repositories.tenant_repository import TenantRepositoryImpl
from app.workers.notification_tasks import send_reservation_notification_task

logger = get_logger(__name__)


class ReservationService:
    def __init__(
        self,
        reservation_repo: ReservationRepositoryImpl,
        resource_repo: ResourceRepositoryImpl,
        tenant_repo: TenantRepositoryImpl,
        redis: Redis,
    ) -> None:
        self._reservation_repo = reservation_repo
        self._resource_repo = resource_repo
        self._tenant_repo = tenant_repo
        self._redis = redis

    async def create_reservation(
        self,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
        data: CreateReservationRequest,
    ) -> ReservationResponse:
        tenant = await self._tenant_repo.get_by_id(tenant_id)
        if not tenant or not tenant.is_active:
            raise ValueError("Tenant not found or inactive")

        resource = await self._resource_repo.get_by_id(data.resource_id)
        if not resource or resource.tenant_id != tenant_id:
            raise ValueError("Resource not found")
        if not resource.is_available:
            raise ValueError("Resource is not available")

        time_slot = TimeSlot(data.start_time, data.end_time)

        # Business rule: advance booking window
        now = datetime.now(UTC)
        min_advance = timedelta(hours=tenant.settings.min_advance_booking_hours)
        if time_slot.start < now + min_advance:
            raise ValueError(
                f"Reservation must be made at least "
                f"{tenant.settings.min_advance_booking_hours} hours in advance"
            )

        max_advance = timedelta(days=tenant.settings.max_advance_booking_days)
        if time_slot.start > now + max_advance:
            raise ValueError(
                f"Reservation cannot be more than "
                f"{tenant.settings.max_advance_booking_days} days in advance"
            )

        # Business rule: customer reservation limit
        active_count = await self._reservation_repo.get_customer_active_count(
            tenant_id, customer_id
        )
        if active_count >= tenant.settings.max_reservations_per_customer:
            raise ValueError(
                f"Maximum {tenant.settings.max_reservations_per_customer} "
                f"active reservations allowed per customer"
            )

        # Check overlap — atomic operation with SELECT FOR UPDATE
        overlapping = await self._reservation_repo.find_overlapping(
            tenant_id, data.resource_id, time_slot
        )
        if overlapping:
            raise ValueError("Requested time slot is not available")

        reference_number = await self._reservation_repo.generate_reference_number(tenant_id)

        reservation = Reservation(
            tenant_id=tenant_id,
            resource_id=data.resource_id,
            customer_id=customer_id,
            time_slot=time_slot,
            reference_number=reference_number,
            notes=data.notes,
        )
        reservation = await self._reservation_repo.save(reservation)

        # Invalidate availability cache
        date_str = time_slot.start.strftime("%Y-%m-%d")
        await self._redis.delete(
            RedisKeys.availability_cache(str(tenant_id), str(data.resource_id), date_str)
        )

        # Dispatch domain events
        for event in reservation.pop_events():
            send_reservation_notification_task.delay(
                event_type=type(event).__name__,
                reservation_id=str(reservation.id),
                tenant_id=str(tenant_id),
                customer_id=str(customer_id),
            )

        logger.info(
            "reservation_created",
            reservation_id=str(reservation.id),
            reference=reference_number,
        )
        return self._to_response(reservation)

    async def cancel_reservation(
        self,
        tenant_id: uuid.UUID,
        reservation_id: uuid.UUID,
        canceller_id: uuid.UUID,
        canceller_role: UserRole,
        data: CancelReservationRequest,
    ) -> ReservationResponse:
        reservation = await self._reservation_repo.get_by_id(reservation_id)
        if not reservation or reservation.tenant_id != tenant_id:
            raise ValueError("Reservation not found")

        if canceller_role == UserRole.CUSTOMER:
            if reservation.customer_id != canceller_id:
                raise PermissionError("Cannot cancel another customer's reservation")

            tenant = await self._tenant_repo.get_by_id(tenant_id)
            if tenant:
                hours_until_start = (
                    reservation.time_slot.start - datetime.now(UTC)
                ).total_seconds() / 3600
                if hours_until_start < tenant.settings.cancellation_hours_before:
                    raise ValueError(
                        f"Cancellation must be made at least "
                        f"{tenant.settings.cancellation_hours_before} hours before start"
                    )

        reservation.cancel(reason=data.reason, cancelled_by=canceller_id)
        reservation = await self._reservation_repo.save(reservation)

        date_str = reservation.time_slot.start.strftime("%Y-%m-%d")
        await self._redis.delete(
            RedisKeys.availability_cache(
                str(tenant_id), str(reservation.resource_id), date_str
            )
        )

        for event in reservation.pop_events():
            send_reservation_notification_task.delay(
                event_type=type(event).__name__,
                reservation_id=str(reservation.id),
                tenant_id=str(tenant_id),
                customer_id=str(reservation.customer_id),
            )

        logger.info("reservation_cancelled", reservation_id=str(reservation_id))
        return self._to_response(reservation)

    async def confirm_reservation(
        self,
        tenant_id: uuid.UUID,
        reservation_id: uuid.UUID,
        confirmed_by: uuid.UUID,
    ) -> ReservationResponse:
        reservation = await self._reservation_repo.get_by_id(reservation_id)
        if not reservation or reservation.tenant_id != tenant_id:
            raise ValueError("Reservation not found")

        reservation.confirm(confirmed_by=confirmed_by)
        reservation = await self._reservation_repo.save(reservation)

        for event in reservation.pop_events():
            send_reservation_notification_task.delay(
                event_type=type(event).__name__,
                reservation_id=str(reservation.id),
                tenant_id=str(tenant_id),
                customer_id=str(reservation.customer_id),
            )

        return self._to_response(reservation)

    async def get_reservation(
        self,
        tenant_id: uuid.UUID,
        reservation_id: uuid.UUID,
        requester_id: uuid.UUID,
        requester_role: UserRole,
    ) -> ReservationResponse:
        reservation = await self._reservation_repo.get_by_id(reservation_id)
        if not reservation or reservation.tenant_id != tenant_id:
            raise ValueError("Reservation not found")

        if requester_role == UserRole.CUSTOMER and reservation.customer_id != requester_id:
            raise PermissionError("Access denied")

        return self._to_response(reservation)

    async def list_reservations(
        self,
        tenant_id: uuid.UUID,
        requester_id: uuid.UUID,
        requester_role: UserRole,
        status: ReservationStatus | None = None,
        resource_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> ReservationListResponse:
        filters: dict[str, object] = {"tenant_id": tenant_id}
        if status:
            filters["status"] = status
        if resource_id:
            filters["resource_id"] = resource_id
        if requester_role == UserRole.CUSTOMER:
            filters["customer_id"] = requester_id

        items, total = await self._reservation_repo.list(offset=offset, limit=limit, **filters)
        return ReservationListResponse(
            items=[self._to_response(r) for r in items],
            total=total,
            offset=offset,
            limit=limit,
        )

    async def get_available_slots(
        self,
        tenant_id: uuid.UUID,
        resource_id: uuid.UUID,
        date_str: str,
    ) -> list[AvailableSlotResponse]:
        cache_key = RedisKeys.availability_cache(str(tenant_id), str(resource_id), date_str)
        cached = await self._redis.get(cache_key)
        if cached:
            import json
            slots_data = json.loads(cached)
            return [AvailableSlotResponse(**s) for s in slots_data]

        resource = await self._resource_repo.get_by_id(resource_id)
        if not resource or resource.tenant_id != tenant_id:
            raise ValueError("Resource not found")

        from datetime import date as date_type
        target_date = date_type.fromisoformat(date_str)
        weekday = target_date.weekday()

        day_hours = resource.working_hours.get_for_weekday(weekday)
        if not day_hours:
            return []

        slots: list[AvailableSlotResponse] = []
        for period in day_hours:
            start_h, start_m = map(int, period["start"].split(":"))
            end_h, end_m = map(int, period["end"].split(":"))

            current = datetime(
                target_date.year, target_date.month, target_date.day,
                start_h, start_m, tzinfo=timezone.utc
            )
            period_end = datetime(
                target_date.year, target_date.month, target_date.day,
                end_h, end_m, tzinfo=timezone.utc
            )

            slot_duration = timedelta(minutes=resource.slot_duration_minutes)
            buffer = timedelta(minutes=resource.buffer_minutes)

            while current + slot_duration <= period_end:
                slot = TimeSlot(current, current + slot_duration)
                overlapping = await self._reservation_repo.find_overlapping(
                    tenant_id, resource_id, slot
                )
                if not overlapping:
                    slots.append(AvailableSlotResponse(
                        start_time=slot.start,
                        end_time=slot.end,
                        resource_id=resource_id,
                        duration_minutes=resource.slot_duration_minutes,
                    ))
                current += slot_duration + buffer

        import json
        await self._redis.setex(
            cache_key,
            30,
            json.dumps([s.model_dump(mode="json") for s in slots]),
        )

        return slots

    @staticmethod
    def _to_response(reservation: Reservation) -> ReservationResponse:
        return ReservationResponse(
            id=reservation.id,
            tenant_id=reservation.tenant_id,
            resource_id=reservation.resource_id,
            customer_id=reservation.customer_id,
            reference_number=reservation.reference_number,
            status=reservation.status,
            start_time=reservation.time_slot.start,
            end_time=reservation.time_slot.end,
            notes=reservation.notes,
            cancellation_reason=reservation.cancellation_reason,
            confirmed_at=reservation.confirmed_at,
            created_at=reservation.created_at,
            updated_at=reservation.updated_at,
        )
