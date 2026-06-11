from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class DomainEvent:
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class ReservationCreatedEvent(DomainEvent):
    reservation_id: uuid.UUID = field(default_factory=uuid.uuid4)
    tenant_id: uuid.UUID = field(default_factory=uuid.uuid4)
    resource_id: uuid.UUID = field(default_factory=uuid.uuid4)
    customer_id: uuid.UUID = field(default_factory=uuid.uuid4)
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    end_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    reference_number: str = ""


@dataclass(frozen=True)
class ReservationConfirmedEvent(DomainEvent):
    reservation_id: uuid.UUID = field(default_factory=uuid.uuid4)
    tenant_id: uuid.UUID = field(default_factory=uuid.uuid4)
    customer_id: uuid.UUID = field(default_factory=uuid.uuid4)
    reference_number: str = ""


@dataclass(frozen=True)
class ReservationCancelledEvent(DomainEvent):
    reservation_id: uuid.UUID = field(default_factory=uuid.uuid4)
    tenant_id: uuid.UUID = field(default_factory=uuid.uuid4)
    customer_id: uuid.UUID = field(default_factory=uuid.uuid4)
    resource_id: uuid.UUID = field(default_factory=uuid.uuid4)
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    end_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    reference_number: str = ""
    reason: str | None = None


@dataclass(frozen=True)
class ReservationUpdatedEvent(DomainEvent):
    reservation_id: uuid.UUID = field(default_factory=uuid.uuid4)
    tenant_id: uuid.UUID = field(default_factory=uuid.uuid4)
    customer_id: uuid.UUID = field(default_factory=uuid.uuid4)
    resource_id: uuid.UUID = field(default_factory=uuid.uuid4)
    old_start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    old_end_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    new_start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    new_end_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    reference_number: str = ""
