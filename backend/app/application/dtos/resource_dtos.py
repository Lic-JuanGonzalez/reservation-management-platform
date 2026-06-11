from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app.domain.entities.resource import ResourceStatus, ResourceType


class WorkingHoursSlot(BaseModel):
    start: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end: str = Field(..., pattern=r"^\d{2}:\d{2}$")


class WorkingHoursRequest(BaseModel):
    monday: list[WorkingHoursSlot] = Field(default_factory=list)
    tuesday: list[WorkingHoursSlot] = Field(default_factory=list)
    wednesday: list[WorkingHoursSlot] = Field(default_factory=list)
    thursday: list[WorkingHoursSlot] = Field(default_factory=list)
    friday: list[WorkingHoursSlot] = Field(default_factory=list)
    saturday: list[WorkingHoursSlot] = Field(default_factory=list)
    sunday: list[WorkingHoursSlot] = Field(default_factory=list)


class CreateResourceRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    resource_type: ResourceType
    description: str | None = Field(default=None, max_length=2000)
    capacity: int = Field(default=1, ge=1, le=10000)
    working_hours: WorkingHoursRequest = Field(default_factory=WorkingHoursRequest)
    amenities: list[str] = Field(default_factory=list)
    slot_duration_minutes: int = Field(default=60, ge=15, le=480)
    buffer_minutes: int = Field(default=0, ge=0, le=120)


class UpdateResourceRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    capacity: int | None = Field(default=None, ge=1)
    working_hours: WorkingHoursRequest | None = None
    amenities: list[str] | None = None
    slot_duration_minutes: int | None = Field(default=None, ge=15, le=480)
    buffer_minutes: int | None = Field(default=None, ge=0, le=120)
    status: ResourceStatus | None = None


class ResourceResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    resource_type: ResourceType
    description: str | None
    capacity: int
    status: ResourceStatus
    amenities: list[str]
    slot_duration_minutes: int
    buffer_minutes: int

    model_config = {"from_attributes": True}


class ResourceListResponse(BaseModel):
    items: list[ResourceResponse]
    total: int
    offset: int
    limit: int
