from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.domain.entities.base import AuditedEntity


class ResourceType(str, Enum):
    ROOM = "room"
    STAFF = "staff"
    EQUIPMENT = "equipment"
    SPACE = "space"
    SERVICE = "service"


class ResourceStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


@dataclass
class WorkingHours:
    monday: list[dict[str, str]] = field(default_factory=list)
    tuesday: list[dict[str, str]] = field(default_factory=list)
    wednesday: list[dict[str, str]] = field(default_factory=list)
    thursday: list[dict[str, str]] = field(default_factory=list)
    friday: list[dict[str, str]] = field(default_factory=list)
    saturday: list[dict[str, str]] = field(default_factory=list)
    sunday: list[dict[str, str]] = field(default_factory=list)

    def get_for_weekday(self, weekday: int) -> list[dict[str, str]]:
        days = [
            self.monday, self.tuesday, self.wednesday,
            self.thursday, self.friday, self.saturday, self.sunday,
        ]
        return days[weekday]


class Resource(AuditedEntity):
    def __init__(
        self,
        tenant_id: uuid.UUID,
        name: str,
        resource_type: ResourceType,
        id: uuid.UUID | None = None,
        description: str | None = None,
        capacity: int = 1,
        status: ResourceStatus = ResourceStatus.ACTIVE,
        working_hours: WorkingHours | None = None,
        amenities: list[str] | None = None,
        image_urls: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        slot_duration_minutes: int = 60,
        buffer_minutes: int = 0,
        **kwargs: object,
    ) -> None:
        super().__init__(id=id, **kwargs)  # type: ignore[arg-type]
        self.tenant_id = tenant_id
        self.name = name
        self.resource_type = resource_type
        self.description = description
        self.capacity = capacity
        self.status = status
        self.working_hours = working_hours or WorkingHours()
        self.amenities: list[str] = amenities or []
        self.image_urls: list[str] = image_urls or []
        self.metadata: dict[str, Any] = metadata or {}
        self.slot_duration_minutes = slot_duration_minutes
        self.buffer_minutes = buffer_minutes

    @property
    def is_available(self) -> bool:
        return self.status == ResourceStatus.ACTIVE

    def activate(self) -> None:
        self.status = ResourceStatus.ACTIVE
        self.touch()

    def deactivate(self) -> None:
        self.status = ResourceStatus.INACTIVE
        self.touch()

    def set_maintenance(self) -> None:
        self.status = ResourceStatus.MAINTENANCE
        self.touch()

    def update(
        self,
        name: str | None = None,
        description: str | None = None,
        capacity: int | None = None,
        amenities: list[str] | None = None,
        slot_duration_minutes: int | None = None,
        buffer_minutes: int | None = None,
        updated_by: uuid.UUID | None = None,
    ) -> None:
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if capacity is not None:
            self.capacity = capacity
        if amenities is not None:
            self.amenities = amenities
        if slot_duration_minutes is not None:
            self.slot_duration_minutes = slot_duration_minutes
        if buffer_minutes is not None:
            self.buffer_minutes = buffer_minutes
        self.touch(updated_by)
