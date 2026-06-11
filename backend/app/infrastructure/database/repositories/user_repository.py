from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User, UserRole, UserStatus
from app.domain.repositories.base import BaseRepository
from app.infrastructure.database.models.user_model import UserModel


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(
                UserModel.id == id,
                UserModel.deleted_at.is_(None),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_email(
        self,
        email: str,
        tenant_id: uuid.UUID | None = None,
    ) -> User | None:
        query = select(UserModel).where(
            UserModel.email == email.lower(),
            UserModel.deleted_at.is_(None),
        )
        if tenant_id is not None:
            query = query.where(UserModel.tenant_id == tenant_id)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, entity: User) -> User:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == entity.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            model = UserModel(
                id=entity.id,
                tenant_id=entity.tenant_id,
                email=entity.email.lower(),
                hashed_password=entity.hashed_password,
                first_name=entity.first_name,
                last_name=entity.last_name,
                role=entity.role.value,
                status=entity.status.value,
                phone=entity.phone,
                avatar_url=entity.avatar_url,
                email_verified=entity.email_verified,
                phone_verified=entity.phone_verified,
                notification_preferences=entity.notification_preferences,
                created_at=entity.created_at,
                updated_at=entity.updated_at,
                created_by=entity.created_by,
                updated_by=entity.updated_by,
                deleted_at=entity.deleted_at,
            )
            self._session.add(model)
        else:
            model.hashed_password = entity.hashed_password
            model.first_name = entity.first_name
            model.last_name = entity.last_name
            model.role = entity.role.value
            model.status = entity.status.value
            model.phone = entity.phone
            model.avatar_url = entity.avatar_url
            model.email_verified = entity.email_verified
            model.phone_verified = entity.phone_verified
            model.notification_preferences = entity.notification_preferences
            model.updated_at = datetime.now(UTC)
            model.updated_by = entity.updated_by
            model.deleted_at = entity.deleted_at

        await self._session.flush()
        return self._to_entity(model)

    async def delete(self, id: uuid.UUID) -> None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.deleted_at = datetime.now(UTC)
            await self._session.flush()

    async def list(
        self,
        offset: int = 0,
        limit: int = 50,
        **filters: object,
    ) -> tuple[list[User], int]:
        query = select(UserModel).where(UserModel.deleted_at.is_(None))

        if "tenant_id" in filters:
            query = query.where(UserModel.tenant_id == filters["tenant_id"])
        if "role" in filters:
            query = query.where(UserModel.role == filters["role"])
        if "status" in filters:
            query = query.where(UserModel.status == filters["status"])

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self._session.execute(count_query)).scalar_one()

        query = query.offset(offset).limit(limit).order_by(UserModel.created_at.desc())
        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models], total

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            hashed_password=model.hashed_password,
            first_name=model.first_name,
            last_name=model.last_name,
            role=UserRole(model.role),
            tenant_id=model.tenant_id,
            status=UserStatus(model.status),
            phone=model.phone,
            avatar_url=model.avatar_url,
            email_verified=model.email_verified,
            phone_verified=model.phone_verified,
            notification_preferences=model.notification_preferences,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by,
            deleted_at=model.deleted_at,
        )
