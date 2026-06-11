from __future__ import annotations

import uuid
from abc import abstractmethod
from datetime import datetime

from app.domain.entities.reservation import Reservation, ReservationStatus
from app.domain.repositories.base import BaseRepository
from app.domain.value_objects.time_slot import TimeSlot


class ReservationRepository(BaseRepository[Reservation]):
    @abstractmethod
    async def get_by_reference(
        self, tenant_id: uuid.UUID, reference_number: str
    ) -> Reservation | None: ...

    @abstractmethod
    async def find_overlapping(
        self,
        tenant_id: uuid.UUID,
        resource_id: uuid.UUID,
        time_slot: TimeSlot,
        exclude_id: uuid.UUID | None = None,
    ) -> list[Reservation]: ...

    @abstractmethod
    async def get_customer_active_count(
        self,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
    ) -> int: ...

    @abstractmethod
    async def get_by_customer(
        self,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
        status: ReservationStatus | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Reservation], int]: ...

    @abstractmethod
    async def get_by_resource(
        self,
        tenant_id: uuid.UUID,
        resource_id: uuid.UUID,
        start_date: datetime,
        end_date: datetime,
        statuses: list[ReservationStatus] | None = None,
    ) -> list[Reservation]: ...

    @abstractmethod
    async def get_upcoming_reminders(
        self,
        remind_at: datetime,
        window_minutes: int = 15,
    ) -> list[Reservation]: ...

    @abstractmethod
    async def generate_reference_number(self, tenant_id: uuid.UUID) -> str: ...
