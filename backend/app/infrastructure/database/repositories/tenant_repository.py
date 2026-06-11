from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.tenant import BusinessType, Tenant, TenantSettings, TenantStatus
from app.domain.repositories.base import BaseRepository
from app.infrastructure.database.models.tenant_model import TenantModel


class TenantRepositoryImpl(BaseRepository[Tenant]):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Tenant | None:
        result = await self._session.execute(
            select(TenantModel).where(
                TenantModel.id == id,
                TenantModel.deleted_at.is_(None),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_slug(self, slug: str) -> Tenant | None:
        result = await self._session.execute(
            select(TenantModel).where(
                TenantModel.slug == slug,
                TenantModel.deleted_at.is_(None),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, entity: Tenant) -> Tenant:
        result = await self._session.execute(
            select(TenantModel).where(TenantModel.id == entity.id)
        )
        model = result.scalar_one_or_none()

        settings_dict = {
            "timezone": entity.settings.timezone,
            "locale": entity.settings.locale,
            "currency": entity.settings.currency,
            "date_format": entity.settings.date_format,
            "time_format": entity.settings.time_format,
            "max_advance_booking_days": entity.settings.max_advance_booking_days,
            "min_advance_booking_hours": entity.settings.min_advance_booking_hours,
            "max_reservations_per_customer": entity.settings.max_reservations_per_customer,
            "cancellation_hours_before": entity.settings.cancellation_hours_before,
            "slot_duration_minutes": entity.settings.slot_duration_minutes,
            "require_email_verification": entity.settings.require_email_verification,
            "allow_guest_bookings": entity.settings.allow_guest_bookings,
            "send_reminders": entity.settings.send_reminders,
            "reminder_hours_before": entity.settings.reminder_hours_before,
        }

        if model is None:
            model = TenantModel(
                id=entity.id,
                name=entity.name,
                slug=entity.slug,
                business_type=entity.business_type.value,
                owner_email=entity.owner_email,
                status=entity.status.value,
                settings=settings_dict,
                logo_url=entity.logo_url,
                website=entity.website,
                phone=entity.phone,
                address=entity.address,
                subscription_id=entity.subscription_id,
                created_at=entity.created_at,
                updated_at=entity.updated_at,
                created_by=entity.created_by,
                updated_by=entity.updated_by,
            )
            self._session.add(model)
        else:
            model.name = entity.name
            model.status = entity.status.value
            model.settings = settings_dict
            model.logo_url = entity.logo_url
            model.website = entity.website
            model.phone = entity.phone
            model.address = entity.address
            model.subscription_id = entity.subscription_id
            model.updated_at = datetime.now(UTC)
            model.updated_by = entity.updated_by
            model.deleted_at = entity.deleted_at

        await self._session.flush()
        return self._to_entity(model)

    async def delete(self, id: uuid.UUID) -> None:
        result = await self._session.execute(
            select(TenantModel).where(TenantModel.id == id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.deleted_at = datetime.now(UTC)
            await self._session.flush()

    async def list(
        self, offset: int = 0, limit: int = 50, **filters: object
    ) -> tuple[list[Tenant], int]:
        query = select(TenantModel).where(TenantModel.deleted_at.is_(None))
        if "status" in filters:
            query = query.where(TenantModel.status == filters["status"])

        count_result = await self._session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        query = query.offset(offset).limit(limit).order_by(TenantModel.created_at.desc())
        result = await self._session.execute(query)
        return [self._to_entity(m) for m in result.scalars().all()], total

    @staticmethod
    def _to_entity(model: TenantModel) -> Tenant:
        s = model.settings or {}
        settings = TenantSettings(
            timezone=s.get("timezone", "UTC"),
            locale=s.get("locale", "en-US"),
            currency=s.get("currency", "USD"),
            date_format=s.get("date_format", "YYYY-MM-DD"),
            time_format=s.get("time_format", "HH:mm"),
            max_advance_booking_days=s.get("max_advance_booking_days", 90),
            min_advance_booking_hours=s.get("min_advance_booking_hours", 1),
            max_reservations_per_customer=s.get("max_reservations_per_customer", 5),
            cancellation_hours_before=s.get("cancellation_hours_before", 24),
            slot_duration_minutes=s.get("slot_duration_minutes", 60),
            require_email_verification=s.get("require_email_verification", True),
            allow_guest_bookings=s.get("allow_guest_bookings", False),
            send_reminders=s.get("send_reminders", True),
            reminder_hours_before=s.get("reminder_hours_before", [24, 1]),
        )
        return Tenant(
            id=model.id,
            name=model.name,
            slug=model.slug,
            business_type=BusinessType(model.business_type),
            owner_email=model.owner_email,
            status=TenantStatus(model.status),
            settings=settings,
            logo_url=model.logo_url,
            website=model.website,
            phone=model.phone,
            address=model.address,
            subscription_id=model.subscription_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by,
            deleted_at=model.deleted_at,
        )
