from __future__ import annotations

import uuid
from enum import Enum

from app.domain.entities.base import AuditedEntity


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    EMPLOYEE = "employee"
    CUSTOMER = "customer"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_VERIFICATION = "pending_verification"
    SUSPENDED = "suspended"


class User(AuditedEntity):
    def __init__(
        self,
        email: str,
        hashed_password: str,
        first_name: str,
        last_name: str,
        role: UserRole,
        tenant_id: uuid.UUID | None = None,
        id: uuid.UUID | None = None,
        status: UserStatus = UserStatus.PENDING_VERIFICATION,
        phone: str | None = None,
        avatar_url: str | None = None,
        email_verified: bool = False,
        phone_verified: bool = False,
        notification_preferences: dict[str, bool] | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(id=id, **kwargs)  # type: ignore[arg-type]
        self.email = email
        self.hashed_password = hashed_password
        self.first_name = first_name
        self.last_name = last_name
        self.role = role
        self.tenant_id = tenant_id
        self.status = status
        self.phone = phone
        self.avatar_url = avatar_url
        self.email_verified = email_verified
        self.phone_verified = phone_verified
        self.notification_preferences: dict[str, bool] = notification_preferences or {
            "email": True,
            "sms": False,
            "push": False,
        }

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE

    def verify_email(self) -> None:
        self.email_verified = True
        if self.status == UserStatus.PENDING_VERIFICATION:
            self.status = UserStatus.ACTIVE
        self.touch()

    def activate(self) -> None:
        self.status = UserStatus.ACTIVE
        self.touch()

    def suspend(self) -> None:
        self.status = UserStatus.SUSPENDED
        self.touch()

    def update_password(self, hashed_password: str) -> None:
        self.hashed_password = hashed_password
        self.touch()

    def update_profile(
        self,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
        avatar_url: str | None = None,
    ) -> None:
        if first_name is not None:
            self.first_name = first_name
        if last_name is not None:
            self.last_name = last_name
        if phone is not None:
            self.phone = phone
        if avatar_url is not None:
            self.avatar_url = avatar_url
        self.touch()

    def can_access_tenant(self, tenant_id: uuid.UUID) -> bool:
        if self.role == UserRole.SUPER_ADMIN:
            return True
        return self.tenant_id == tenant_id

    def has_permission(self, permission: str) -> bool:
        role_permissions: dict[UserRole, set[str]] = {
            UserRole.SUPER_ADMIN: {"*"},
            UserRole.TENANT_ADMIN: {
                "tenants:read", "tenants:update",
                "users:*", "resources:*", "reservations:*",
                "reports:*", "settings:*",
            },
            UserRole.EMPLOYEE: {
                "users:read", "resources:read",
                "reservations:read", "reservations:create",
                "reservations:update", "reservations:cancel",
            },
            UserRole.CUSTOMER: {
                "reservations:read", "reservations:create",
                "reservations:cancel", "profile:*",
            },
        }
        perms = role_permissions.get(self.role, set())
        return "*" in perms or permission in perms or f"{permission.split(':')[0]}:*" in perms
