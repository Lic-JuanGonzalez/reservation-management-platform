from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.domain.entities.base import AuditedEntity


class TenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    TRIAL = "trial"


class BusinessType(str, Enum):
    HOTEL = "hotel"
    MEDICAL_CLINIC = "medical_clinic"
    DENTAL_OFFICE = "dental_office"
    GYM = "gym"
    BEAUTY_SALON = "beauty_salon"
    COWORKING = "coworking"
    EVENT_VENUE = "event_venue"
    PROFESSIONAL_SERVICES = "professional_services"
    OTHER = "other"


@dataclass
class TenantSettings:
    timezone: str = "UTC"
    locale: str = "en-US"
    currency: str = "USD"
    date_format: str = "YYYY-MM-DD"
    time_format: str = "HH:mm"
    max_advance_booking_days: int = 90
    min_advance_booking_hours: int = 1
    max_reservations_per_customer: int = 5
    cancellation_hours_before: int = 24
    slot_duration_minutes: int = 60
    require_email_verification: bool = True
    allow_guest_bookings: bool = False
    send_reminders: bool = True
    reminder_hours_before: list[int] = field(default_factory=lambda: [24, 1])


class Tenant(AuditedEntity):
    def __init__(
        self,
        name: str,
        slug: str,
        business_type: BusinessType,
        owner_email: str,
        id: uuid.UUID | None = None,
        status: TenantStatus = TenantStatus.TRIAL,
        settings: TenantSettings | None = None,
        logo_url: str | None = None,
        website: str | None = None,
        phone: str | None = None,
        address: str | None = None,
        subscription_id: uuid.UUID | None = None,
        trial_ends_at: datetime | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(id=id, **kwargs)  # type: ignore[arg-type]
        self.name = name
        self.slug = slug
        self.business_type = business_type
        self.owner_email = owner_email
        self.status = status
        self.settings = settings or TenantSettings()
        self.logo_url = logo_url
        self.website = website
        self.phone = phone
        self.address = address
        self.subscription_id = subscription_id
        self.trial_ends_at = trial_ends_at

    def activate(self) -> None:
        self.status = TenantStatus.ACTIVE
        self.touch()

    def suspend(self) -> None:
        self.status = TenantStatus.SUSPENDED
        self.touch()

    def cancel(self) -> None:
        self.status = TenantStatus.CANCELLED
        self.touch()

    @property
    def is_active(self) -> bool:
        return self.status in (TenantStatus.ACTIVE, TenantStatus.TRIAL)

    def update_settings(self, **kwargs: object) -> None:
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
        self.touch()
