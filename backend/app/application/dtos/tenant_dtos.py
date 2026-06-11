from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field

from app.domain.entities.tenant import BusinessType, TenantStatus


class CreateTenantRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    business_type: BusinessType
    owner_email: EmailStr
    owner_first_name: str = Field(..., min_length=1, max_length=100)
    owner_last_name: str = Field(..., min_length=1, max_length=100)
    owner_password: str = Field(..., min_length=8)
    phone: str | None = None
    website: str | None = None
    address: str | None = None


class UpdateTenantRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    logo_url: str | None = None
    website: str | None = None
    phone: str | None = None
    address: str | None = None


class UpdateTenantSettingsRequest(BaseModel):
    timezone: str | None = None
    locale: str | None = None
    currency: str | None = None
    max_advance_booking_days: int | None = Field(default=None, ge=1, le=365)
    min_advance_booking_hours: int | None = Field(default=None, ge=0, le=720)
    max_reservations_per_customer: int | None = Field(default=None, ge=1, le=100)
    cancellation_hours_before: int | None = Field(default=None, ge=0, le=720)
    slot_duration_minutes: int | None = Field(default=None, ge=15, le=480)
    send_reminders: bool | None = None
    reminder_hours_before: list[int] | None = None


class TenantSettingsResponse(BaseModel):
    timezone: str
    locale: str
    currency: str
    date_format: str
    time_format: str
    max_advance_booking_days: int
    min_advance_booking_hours: int
    max_reservations_per_customer: int
    cancellation_hours_before: int
    slot_duration_minutes: int
    require_email_verification: bool
    allow_guest_bookings: bool
    send_reminders: bool
    reminder_hours_before: list[int]

    model_config = {"from_attributes": True}


class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    business_type: BusinessType
    status: TenantStatus
    owner_email: str
    logo_url: str | None
    website: str | None
    phone: str | None
    address: str | None
    settings: TenantSettingsResponse

    model_config = {"from_attributes": True}


class TenantListResponse(BaseModel):
    items: list[TenantResponse]
    total: int
    offset: int
    limit: int
