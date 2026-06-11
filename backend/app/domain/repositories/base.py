from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from app.domain.entities.base import AuditedEntity

T = TypeVar("T", bound=AuditedEntity)


class BaseRepository(ABC, Generic[T]):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> T | None: ...

    @abstractmethod
    async def save(self, entity: T) -> T: ...

    @abstractmethod
    async def delete(self, id: uuid.UUID) -> None: ...

    @abstractmethod
    async def list(
        self,
        offset: int = 0,
        limit: int = 50,
        **filters: object,
    ) -> tuple[list[T], int]: ...
