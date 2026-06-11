from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.reservation import Reservation, ReservationStatus
from app.domain.repositories.reservation_repository import ReservationRepository
from app.domain.value_objects.time_slot import TimeSlot
from app.infrastructure.database.models.reservation_model import ReservationModel


class ReservationRepositoryImpl(ReservationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Reservation | None:
        result = await self._session.execute(
            select(ReservationModel).where(
                ReservationModel.id == id,
                ReservationModel.deleted_at.is_(None),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_reference(
        self, tenant_id: uuid.UUID, reference_number: str
    ) -> Reservation | None:
        result = await self._session.execute(
            select(ReservationModel).where(
                ReservationModel.tenant_id == tenant_id,
                ReservationModel.reference_number == reference_number,
                ReservationModel.deleted_at.is_(None),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_overlapping(
        self,
        tenant_id: uuid.UUID,
        resource_id: uuid.UUID,
        time_slot: TimeSlot,
        exclude_id: uuid.UUID | None = None,
    ) -> list[Reservation]:
        query = select(ReservationModel).where(
            ReservationModel.tenant_id == tenant_id,
            ReservationModel.resource_id == resource_id,
            ReservationModel.status.in_([
                ReservationStatus.PENDING.value,
                ReservationStatus.CONFIRMED.value,
            ]),
            ReservationModel.deleted_at.is_(None),
            ReservationModel.start_time < time_slot.end,
            ReservationModel.end_time > time_slot.start,
        ).with_for_update(skip_locked=True)

        if exclude_id:
            query = query.where(ReservationModel.id != exclude_id)

        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_customer_active_count(
        self, tenant_id: uuid.UUID, customer_id: uuid.UUID
    ) -> int:
        result = await self._session.execute(
            select(func.count()).where(
                ReservationModel.tenant_id == tenant_id,
                ReservationModel.customer_id == customer_id,
                ReservationModel.status.in_([
                    ReservationStatus.PENDING.value,
                    ReservationStatus.CONFIRMED.value,
                ]),
                ReservationModel.deleted_at.is_(None),
            )
        )
        return result.scalar_one()

    async def get_by_customer(
        self,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
        status: ReservationStatus | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Reservation], int]:
        query = select(ReservationModel).where(
            ReservationModel.tenant_id == tenant_id,
            ReservationModel.customer_id == customer_id,
            ReservationModel.deleted_at.is_(None),
        )
        if status:
            query = query.where(ReservationModel.status == status.value)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self._session.execute(count_query)).scalar_one()

        query = query.offset(offset).limit(limit).order_by(
            ReservationModel.start_time.desc()
        )
        result = await self._session.execute(query)
        return [self._to_entity(m) for m in result.scalars().all()], total

    async def get_by_resource(
        self,
        tenant_id: uuid.UUID,
        resource_id: uuid.UUID,
        start_date: datetime,
        end_date: datetime,
        statuses: list[ReservationStatus] | None = None,
    ) -> list[Reservation]:
        query = select(ReservationModel).where(
            ReservationModel.tenant_id == tenant_id,
            ReservationModel.resource_id == resource_id,
            ReservationModel.start_time >= start_date,
            ReservationModel.end_time <= end_date,
            ReservationModel.deleted_at.is_(None),
        )
        if statuses:
            query = query.where(
                ReservationModel.status.in_([s.value for s in statuses])
            )
        result = await self._session.execute(query.order_by(ReservationModel.start_time))
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_upcoming_reminders(
        self, remind_at: datetime, window_minutes: int = 15
    ) -> list[Reservation]:
        from datetime import timedelta
        window_end = remind_at + timedelta(minutes=window_minutes)
        result = await self._session.execute(
            select(ReservationModel).where(
                ReservationModel.status == ReservationStatus.CONFIRMED.value,
                ReservationModel.start_time.between(remind_at, window_end),
                ReservationModel.deleted_at.is_(None),
            )
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def generate_reference_number(self, tenant_id: uuid.UUID) -> str:
        result = await self._session.execute(
            text(
                "SELECT nextval('reservation_reference_seq') AS seq"
            )
        )
        seq = result.scalar_one()
        prefix = str(tenant_id).replace("-", "")[:6].upper()
        return f"{prefix}-{seq:08d}"

    async def save(self, entity: Reservation) -> Reservation:
        result = await self._session.execute(
            select(ReservationModel).where(ReservationModel.id == entity.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            model = ReservationModel(
                id=entity.id,
                tenant_id=entity.tenant_id,
                resource_id=entity.resource_id,
                customer_id=entity.customer_id,
                reference_number=entity.reference_number,
                status=entity.status.value,
                start_time=entity.time_slot.start,
                end_time=entity.time_slot.end,
                notes=entity.notes,
                internal_notes=entity.internal_notes,
                cancellation_reason=entity.cancellation_reason,
                cancelled_by=entity.cancelled_by,
                cancelled_at=entity.cancelled_at,
                confirmed_at=entity.confirmed_at,
                completed_at=entity.completed_at,
                metadata_=entity.metadata,
                created_at=entity.created_at,
                updated_at=entity.updated_at,
                created_by=entity.created_by,
                updated_by=entity.updated_by,
            )
            self._session.add(model)
        else:
            model.status = entity.status.value
            model.start_time = entity.time_slot.start
            model.end_time = entity.time_slot.end
            model.notes = entity.notes
            model.internal_notes = entity.internal_notes
            model.cancellation_reason = entity.cancellation_reason
            model.cancelled_by = entity.cancelled_by
            model.cancelled_at = entity.cancelled_at
            model.confirmed_at = entity.confirmed_at
            model.completed_at = entity.completed_at
            model.metadata_ = entity.metadata
            model.updated_at = datetime.now(UTC)
            model.updated_by = entity.updated_by

        await self._session.flush()
        return self._to_entity(model)

    async def delete(self, id: uuid.UUID) -> None:
        result = await self._session.execute(
            select(ReservationModel).where(ReservationModel.id == id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.deleted_at = datetime.now(UTC)
            await self._session.flush()

    async def list(
        self, offset: int = 0, limit: int = 50, **filters: object
    ) -> tuple[list[Reservation], int]:
        query = select(ReservationModel).where(ReservationModel.deleted_at.is_(None))
        if "tenant_id" in filters:
            query = query.where(ReservationModel.tenant_id == filters["tenant_id"])
        if "customer_id" in filters:
            query = query.where(ReservationModel.customer_id == filters["customer_id"])
        if "resource_id" in filters:
            query = query.where(ReservationModel.resource_id == filters["resource_id"])
        if "status" in filters:
            query = query.where(ReservationModel.status == filters["status"])

        count_result = await self._session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        query = query.offset(offset).limit(limit).order_by(
            ReservationModel.start_time.desc()
        )
        result = await self._session.execute(query)
        return [self._to_entity(m) for m in result.scalars().all()], total

    @staticmethod
    def _to_entity(model: ReservationModel) -> Reservation:
        return Reservation(
            id=model.id,
            tenant_id=model.tenant_id,
            resource_id=model.resource_id,
            customer_id=model.customer_id,
            reference_number=model.reference_number,
            time_slot=TimeSlot(model.start_time, model.end_time),  # type: ignore[arg-type]
            status=ReservationStatus(model.status),
            notes=model.notes,
            internal_notes=model.internal_notes,
            cancellation_reason=model.cancellation_reason,
            cancelled_by=model.cancelled_by,
            cancelled_at=model.cancelled_at,
            confirmed_at=model.confirmed_at,
            completed_at=model.completed_at,
            metadata=model.metadata_,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by,
            deleted_at=model.deleted_at,
        )
