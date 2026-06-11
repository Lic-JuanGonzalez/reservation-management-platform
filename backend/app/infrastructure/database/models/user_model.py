from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, JSON, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.entities.user import UserRole, UserStatus
from app.infrastructure.database.models.base import AuditMixin, Base


class UserModel(AuditMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", "tenant_id", name="uq_users_email_tenant"),
        {"schema": "public"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.tenants.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum(UserRole, name="user_role_enum", values_callable=lambda x: [e.value for e in x], create_type=False), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        Enum(UserStatus, name="user_status_enum", values_callable=lambda x: [e.value for e in x], create_type=False),
        nullable=False,
        default=UserStatus.PENDING_VERIFICATION,
        index=True,
    )
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notification_preferences: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    tenant: Mapped["TenantModel"] = relationship(  # type: ignore[name-defined]
        "TenantModel", back_populates="users", lazy="noload"
    )
    reservations: Mapped[list["ReservationModel"]] = relationship(  # type: ignore[name-defined]
        "ReservationModel", back_populates="customer", lazy="noload"
    )
