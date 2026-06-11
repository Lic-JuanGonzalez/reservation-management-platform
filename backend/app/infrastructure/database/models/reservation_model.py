from __future__ import annotations

import uuid

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.entities.reservation import ReservationStatus
from app.infrastructure.database.models.base import AuditMixin, Base


class ReservationModel(AuditMixin, Base):
    __tablename__ = "reservations"
    __table_args__ = (
        UniqueConstraint("reference_number", "tenant_id", name="uq_reservations_reference_tenant"),
        {"schema": "public"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.resources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reference_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        Enum(ReservationStatus, name="reservation_status_enum", values_callable=lambda x: [e.value for e in x], create_type=False),
        nullable=False,
        default=ReservationStatus.PENDING,
        index=True,
    )
    start_time: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    end_time: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelled_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    cancelled_at: Mapped[object | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    confirmed_at: Mapped[object | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[object | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )

    tenant: Mapped["TenantModel"] = relationship("TenantModel", lazy="noload")  # type: ignore[name-defined]
    resource: Mapped["ResourceModel"] = relationship(  # type: ignore[name-defined]
        "ResourceModel", back_populates="reservations", lazy="noload"
    )
    customer: Mapped["UserModel"] = relationship(  # type: ignore[name-defined]
        "UserModel", back_populates="reservations", lazy="noload"
    )
