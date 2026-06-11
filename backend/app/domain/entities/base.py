from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any


class Entity:
    def __init__(self, id: uuid.UUID | None = None) -> None:
        self._id: uuid.UUID = id or uuid.uuid4()
        self._events: list[Any] = []

    @property
    def id(self) -> uuid.UUID:
        return self._id

    def add_event(self, event: Any) -> None:
        self._events.append(event)

    def pop_events(self) -> list[Any]:
        events = self._events.copy()
        self._events.clear()
        return events

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)


class AuditedEntity(Entity):
    def __init__(
        self,
        id: uuid.UUID | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        created_by: uuid.UUID | None = None,
        updated_by: uuid.UUID | None = None,
        deleted_at: datetime | None = None,
    ) -> None:
        super().__init__(id)
        self.created_at: datetime = created_at or datetime.now(UTC)
        self.updated_at: datetime = updated_at or datetime.now(UTC)
        self.created_by: uuid.UUID | None = created_by
        self.updated_by: uuid.UUID | None = updated_by
        self.deleted_at: datetime | None = deleted_at

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self, deleted_by: uuid.UUID | None = None) -> None:
        self.deleted_at = datetime.now(UTC)
        if deleted_by:
            self.updated_by = deleted_by
        self.updated_at = datetime.now(UTC)

    def touch(self, updated_by: uuid.UUID | None = None) -> None:
        self.updated_at = datetime.now(UTC)
        if updated_by:
            self.updated_by = updated_by
