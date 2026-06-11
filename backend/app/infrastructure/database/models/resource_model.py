from __future__ import annotations

import uuid

from sqlalchemy import Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.entities.resource import ResourceStatus, ResourceType
from app.infrastructure.database.models.base import AuditMixin, Base


class ResourceModel(AuditMixin, Base):
    __tablename__ = "resources"
    __table_args__ = {"schema": "public"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[str] = mapped_column(
        Enum(ResourceType, name="resource_type_enum", values_callable=lambda x: [e.value for e in x], create_type=False), nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(
        Enum(ResourceStatus, name="resource_status_enum", values_callable=lambda x: [e.value for e in x], create_type=False),
        nullable=False,
        default=ResourceStatus.ACTIVE,
        index=True,
    )
    working_hours: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    amenities: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    image_urls: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )
    slot_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    buffer_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    tenant: Mapped["TenantModel"] = relationship(  # type: ignore[name-defined]
        "TenantModel", back_populates="resources", lazy="noload"
    )
    reservations: Mapped[list["ReservationModel"]] = relationship(  # type: ignore[name-defined]
        "ReservationModel", back_populates="resource", lazy="noload"
    )
    availability_rules: Mapped[list["AvailabilityRuleModel"]] = relationship(  # type: ignore[name-defined]
        "AvailabilityRuleModel", back_populates="resource", lazy="noload"
    )
