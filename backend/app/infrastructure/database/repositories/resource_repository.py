from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.resource import Resource, ResourceStatus, ResourceType, WorkingHours
from app.domain.repositories.base import BaseRepository
from app.infrastructure.database.models.resource_model import ResourceModel


class ResourceRepositoryImpl(BaseRepository[Resource]):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Resource | None:
        result = await self._session.execute(
            select(ResourceModel).where(
                ResourceModel.id == id,
                ResourceModel.deleted_at.is_(None),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, entity: Resource) -> Resource:
        result = await self._session.execute(
            select(ResourceModel).where(ResourceModel.id == entity.id)
        )
        model = result.scalar_one_or_none()

        working_hours_dict = {
            "monday": entity.working_hours.monday,
            "tuesday": entity.working_hours.tuesday,
            "wednesday": entity.working_hours.wednesday,
            "thursday": entity.working_hours.thursday,
            "friday": entity.working_hours.friday,
            "saturday": entity.working_hours.saturday,
            "sunday": entity.working_hours.sunday,
        }

        if model is None:
            model = ResourceModel(
                id=entity.id,
                tenant_id=entity.tenant_id,
                name=entity.name,
                resource_type=entity.resource_type.value,
                description=entity.description,
                capacity=entity.capacity,
                status=entity.status.value,
                working_hours=working_hours_dict,
                amenities=entity.amenities,
                image_urls=entity.image_urls,
                metadata_=entity.metadata,
                slot_duration_minutes=entity.slot_duration_minutes,
                buffer_minutes=entity.buffer_minutes,
                created_at=entity.created_at,
                updated_at=entity.updated_at,
                created_by=entity.created_by,
                updated_by=entity.updated_by,
            )
            self._session.add(model)
        else:
            model.name = entity.name
            model.description = entity.description
            model.capacity = entity.capacity
            model.status = entity.status.value
            model.working_hours = working_hours_dict
            model.amenities = entity.amenities
            model.image_urls = entity.image_urls
            model.metadata_ = entity.metadata
            model.slot_duration_minutes = entity.slot_duration_minutes
            model.buffer_minutes = entity.buffer_minutes
            model.updated_at = datetime.now(UTC)
            model.updated_by = entity.updated_by
            model.deleted_at = entity.deleted_at

        await self._session.flush()
        return self._to_entity(model)

    async def delete(self, id: uuid.UUID) -> None:
        result = await self._session.execute(
            select(ResourceModel).where(ResourceModel.id == id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.deleted_at = datetime.now(UTC)
            await self._session.flush()

    async def list(
        self, offset: int = 0, limit: int = 50, **filters: object
    ) -> tuple[list[Resource], int]:
        query = select(ResourceModel).where(ResourceModel.deleted_at.is_(None))
        if "tenant_id" in filters:
            query = query.where(ResourceModel.tenant_id == filters["tenant_id"])
        if "status" in filters:
            query = query.where(ResourceModel.status == filters["status"])
        if "resource_type" in filters:
            query = query.where(ResourceModel.resource_type == filters["resource_type"])

        count_result = await self._session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        query = query.offset(offset).limit(limit).order_by(ResourceModel.name)
        result = await self._session.execute(query)
        return [self._to_entity(m) for m in result.scalars().all()], total

    @staticmethod
    def _to_entity(model: ResourceModel) -> Resource:
        wh = model.working_hours or {}
        working_hours = WorkingHours(
            monday=wh.get("monday", []),
            tuesday=wh.get("tuesday", []),
            wednesday=wh.get("wednesday", []),
            thursday=wh.get("thursday", []),
            friday=wh.get("friday", []),
            saturday=wh.get("saturday", []),
            sunday=wh.get("sunday", []),
        )
        return Resource(
            id=model.id,
            tenant_id=model.tenant_id,
            name=model.name,
            resource_type=ResourceType(model.resource_type),
            description=model.description,
            capacity=model.capacity,
            status=ResourceStatus(model.status),
            working_hours=working_hours,
            amenities=model.amenities or [],
            image_urls=model.image_urls or [],
            metadata=model.metadata_ or {},
            slot_duration_minutes=model.slot_duration_minutes,
            buffer_minutes=model.buffer_minutes,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by,
            deleted_at=model.deleted_at,
        )
