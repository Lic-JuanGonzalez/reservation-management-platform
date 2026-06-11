from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from app.domain.entities.base import AuditedEntity
from app.domain.events.reservation_events import (
    ReservationCancelledEvent,
    ReservationConfirmedEvent,
    ReservationCreatedEvent,
    ReservationUpdatedEvent,
)
from app.domain.value_objects.time_slot import TimeSlot


class ReservationStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    WAITLISTED = "waitlisted"


class Reservation(AuditedEntity):
    def __init__(
        self,
        tenant_id: uuid.UUID,
        resource_id: uuid.UUID,
        customer_id: uuid.UUID,
        time_slot: TimeSlot,
        reference_number: str,
        id: uuid.UUID | None = None,
        status: ReservationStatus = ReservationStatus.PENDING,
        notes: str | None = None,
        internal_notes: str | None = None,
        cancellation_reason: str | None = None,
        cancelled_by: uuid.UUID | None = None,
        cancelled_at: datetime | None = None,
        confirmed_at: datetime | None = None,
        completed_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(id=id, **kwargs)  # type: ignore[arg-type]
        self.tenant_id = tenant_id
        self.resource_id = resource_id
        self.customer_id = customer_id
        self.time_slot = time_slot
        self.reference_number = reference_number
        self.status = status
        self.notes = notes
        self.internal_notes = internal_notes
        self.cancellation_reason = cancellation_reason
        self.cancelled_by = cancelled_by
        self.cancelled_at = cancelled_at
        self.confirmed_at = confirmed_at
        self.completed_at = completed_at
        self.metadata: dict[str, Any] = metadata or {}

        self.add_event(
            ReservationCreatedEvent(
                reservation_id=self._id,
                tenant_id=tenant_id,
                resource_id=resource_id,
                customer_id=customer_id,
                start_time=time_slot.start,
                end_time=time_slot.end,
                reference_number=reference_number,
            )
        )

    @property
    def is_active(self) -> bool:
        return self.status in (ReservationStatus.PENDING, ReservationStatus.CONFIRMED)

    @property
    def is_cancellable(self) -> bool:
        return self.status in (ReservationStatus.PENDING, ReservationStatus.CONFIRMED)

    def confirm(self, confirmed_by: uuid.UUID | None = None) -> None:
        if self.status != ReservationStatus.PENDING:
            raise ValueError(f"Cannot confirm reservation in status {self.status}")
        from datetime import UTC
        self.status = ReservationStatus.CONFIRMED
        self.confirmed_at = datetime.now(UTC)
        self.touch(confirmed_by)
        self.add_event(
            ReservationConfirmedEvent(
                reservation_id=self._id,
                tenant_id=self.tenant_id,
                customer_id=self.customer_id,
                reference_number=self.reference_number,
            )
        )

    def cancel(
        self,
        reason: str | None = None,
        cancelled_by: uuid.UUID | None = None,
    ) -> None:
        if not self.is_cancellable:
            raise ValueError(f"Cannot cancel reservation in status {self.status}")
        from datetime import UTC
        self.status = ReservationStatus.CANCELLED
        self.cancellation_reason = reason
        self.cancelled_by = cancelled_by
        self.cancelled_at = datetime.now(UTC)
        self.touch(cancelled_by)
        self.add_event(
            ReservationCancelledEvent(
                reservation_id=self._id,
                tenant_id=self.tenant_id,
                customer_id=self.customer_id,
                resource_id=self.resource_id,
                start_time=self.time_slot.start,
                end_time=self.time_slot.end,
                reference_number=self.reference_number,
                reason=reason,
            )
        )

    def complete(self) -> None:
        if self.status != ReservationStatus.CONFIRMED:
            raise ValueError(f"Cannot complete reservation in status {self.status}")
        from datetime import UTC
        self.status = ReservationStatus.COMPLETED
        self.completed_at = datetime.now(UTC)
        self.touch()

    def update_time_slot(
        self,
        new_slot: TimeSlot,
        updated_by: uuid.UUID | None = None,
    ) -> None:
        if not self.is_active:
            raise ValueError(f"Cannot update reservation in status {self.status}")
        old_slot = self.time_slot
        self.time_slot = new_slot
        self.touch(updated_by)
        self.add_event(
            ReservationUpdatedEvent(
                reservation_id=self._id,
                tenant_id=self.tenant_id,
                customer_id=self.customer_id,
                resource_id=self.resource_id,
                old_start_time=old_slot.start,
                old_end_time=old_slot.end,
                new_start_time=new_slot.start,
                new_end_time=new_slot.end,
                reference_number=self.reference_number,
            )
        )
