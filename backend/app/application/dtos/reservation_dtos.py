from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.domain.entities.reservation import ReservationStatus


class CreateReservationRequest(BaseModel):
    resource_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    notes: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_time_range(self) -> "CreateReservationRequest":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        duration_hours = (self.end_time - self.start_time).total_seconds() / 3600
        if duration_hours > 24:
            raise ValueError("Reservation cannot exceed 24 hours")
        return self


class UpdateReservationRequest(BaseModel):
    start_time: datetime | None = None
    end_time: datetime | None = None
    notes: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_time_range(self) -> "UpdateReservationRequest":
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValueError("end_time must be after start_time")
        return self


class CancelReservationRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class ReservationResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    resource_id: uuid.UUID
    customer_id: uuid.UUID
    reference_number: str
    status: ReservationStatus
    start_time: datetime
    end_time: datetime
    notes: str | None
    cancellation_reason: str | None
    confirmed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReservationListResponse(BaseModel):
    items: list[ReservationResponse]
    total: int
    offset: int
    limit: int


class AvailableSlotResponse(BaseModel):
    start_time: datetime
    end_time: datetime
    resource_id: uuid.UUID
    duration_minutes: int


class AvailabilityRequest(BaseModel):
    resource_id: uuid.UUID
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
