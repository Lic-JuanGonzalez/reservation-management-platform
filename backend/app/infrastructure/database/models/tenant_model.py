from __future__ import annotations

import uuid

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.entities.tenant import BusinessType, TenantStatus
from app.infrastructure.database.models.base import AuditMixin, Base


class TenantModel(AuditMixin, Base):
    __tablename__ = "tenants"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_tenants_slug"),
        {"schema": "public"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    business_type: Mapped[str] = mapped_column(
        Enum(BusinessType, name="business_type_enum", values_callable=lambda x: [e.value for e in x], create_type=False), nullable=False
    )
    owner_email: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(TenantStatus, name="tenant_status_enum", values_callable=lambda x: [e.value for e in x], create_type=False),
        nullable=False,
        default=TenantStatus.TRIAL,
        index=True,
    )
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    users: Mapped[list["UserModel"]] = relationship(  # type: ignore[name-defined]
        "UserModel", back_populates="tenant", lazy="noload"
    )
    resources: Mapped[list["ResourceModel"]] = relationship(  # type: ignore[name-defined]
        "ResourceModel", back_populates="tenant", lazy="noload"
    )
